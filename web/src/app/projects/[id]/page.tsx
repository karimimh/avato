"use client";

/* eslint-disable @next/next/no-img-element -- private signed object URLs are transient. */

import {
  ArrowRight,
  Check,
  ChevronLeft,
  ChevronRight,
  Download,
  Film,
  Image as ImageIcon,
  LoaderCircle,
  Mic2,
  Music2,
  Play,
  RefreshCw,
  Save,
  Scissors,
  Share2,
  ShieldCheck,
  Sparkles,
  Star,
  Trash2,
  Upload,
  WandSparkles,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  apiRequest,
  type Project,
  replaceMedia,
  updateProject,
} from "@/lib/api";

type Word = {
  id: string;
  text: string;
  confidence: number;
  start_ms: number;
  end_ms: number;
};
type Segment = {
  id: string;
  position: number;
  start_ms: number;
  end_ms: number;
  text: string;
  original_text: string;
  words: Word[];
};
type Media = {
  id: string;
  kind: "photo" | "clip";
  position: number;
  url: string;
  original_filename: string;
};
type AudioAsset = {
  id: string;
  kind: string;
  url: string;
  duration_ms: number;
  trim_start_ms: number;
  trim_end_ms: number | null;
  analysis: { warning?: string | null };
};
type RenderJob = {
  id: string;
  status: string;
  progress: number;
  tier: string;
  error_detail: string | null;
};
type ExportItem = {
  id: string;
  tier: string;
  width: number;
  height: number;
  watermarked: boolean;
};
type Assignment = {
  segment_id: string;
  media_id: string;
  source: string;
  reused: boolean;
};

const templates = [
  ["clean-story", "روایت ساده"],
  ["dynamic-voice", "صدای پویا"],
  ["memory-film", "فیلم خاطره"],
];

export default function ProjectEditorPage() {
  const projectId = useParams<{ id: string }>().id;
  const router = useRouter();
  const [token] = useState(() =>
    typeof window === "undefined"
      ? ""
      : (window.sessionStorage.getItem("avato_token") ?? ""),
  );
  const [project, setProject] = useState<Project | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [media, setMedia] = useState<Media[]>([]);
  const [audio, setAudio] = useState<AudioAsset[]>([]);
  const [exports, setExports] = useState<ExportItem[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [job, setJob] = useState<RenderJob | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [trim, setTrim] = useState({ start: 0, end: 0 });
  const [previewUrls, setPreviewUrls] = useState<Record<string, string>>({});

  const load = useCallback(
    async (authToken: string) => {
      try {
        const [
          projectData,
          transcriptData,
          mediaData,
          audioData,
          exportData,
          draftData,
        ] = await Promise.all([
          apiRequest<Project>(`/projects/${projectId}`, {}, authToken),
          apiRequest<{ segments: Segment[] }>(
            `/projects/${projectId}/transcript`,
            {},
            authToken,
          ),
          apiRequest<{ items: Media[] }>(
            `/projects/${projectId}/media`,
            {},
            authToken,
          ),
          apiRequest<AudioAsset[]>(
            `/projects/${projectId}/audio`,
            {},
            authToken,
          ),
          apiRequest<ExportItem[]>(
            `/projects/${projectId}/exports`,
            {},
            authToken,
          ),
          apiRequest<{ assignments: Assignment[] }>(
            `/projects/${projectId}/draft`,
            {},
            authToken,
          ),
        ]);
        setProject(projectData);
        setSegments(transcriptData.segments);
        setMedia(mediaData.items);
        setAudio(audioData);
        const original = audioData.find((item) => item.kind === "original");
        if (original) {
          setTrim({
            start: original.trim_start_ms,
            end: original.trim_end_ms ?? original.duration_ms,
          });
        }
        setExports(exportData);
        setAssignments(draftData.assignments);
      } catch (caught) {
        setError(
          caught instanceof Error ? caught.message : "پروژه بارگذاری نشد.",
        );
      }
    },
    [projectId],
  );

  useEffect(() => {
    if (!token) return router.replace("/projects");
    const timer = window.setTimeout(() => void load(token), 0);
    return () => window.clearTimeout(timer);
  }, [load, router, token]);

  useEffect(() => {
    if (!job || !token || !["queued", "running"].includes(job.status)) return;
    const timer = window.setInterval(async () => {
      const current = await apiRequest<RenderJob>(
        `/projects/${projectId}/exports/${job.id}`,
        {},
        token,
      );
      setJob(current);
      if (current.status === "succeeded") {
        setExports(
          await apiRequest<ExportItem[]>(
            `/projects/${projectId}/exports`,
            {},
            token,
          ),
        );
      }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [job, projectId, token]);

  async function saveSettings(changes: Record<string, string | null>) {
    if (!project) return;
    setBusy(true);
    try {
      setProject(await updateProject(token, project.id, changes));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "تغییر ذخیره نشد.");
    } finally {
      setBusy(false);
    }
  }

  async function saveSegment(segment: Segment) {
    const updated = await apiRequest<Segment>(
      `/projects/${projectId}/transcript/segments/${segment.id}`,
      { method: "PATCH", body: JSON.stringify({ text: segment.text }) },
      token,
    );
    setSegments((items) =>
      items.map((item) => (item.id === updated.id ? updated : item)),
    );
  }

  async function restoreTranscript() {
    const result = await apiRequest<{ segments: Segment[] }>(
      `/projects/${projectId}/transcript/restore`,
      { method: "POST", body: "{}" },
      token,
    );
    setSegments(result.segments);
  }

  async function splitTranscript(segment: Segment) {
    const middle = Math.floor(segment.text.length / 2);
    const nextSpace = segment.text.indexOf(" ", middle);
    const characterIndex = nextSpace > 0 ? nextSpace : middle;
    const result = await apiRequest<{ segments: Segment[] }>(
      `/projects/${projectId}/transcript/segments/${segment.id}/split`,
      {
        method: "POST",
        body: JSON.stringify({ character_index: characterIndex }),
      },
      token,
    );
    setSegments(result.segments);
  }

  async function mergeTranscript(segment: Segment, next: Segment) {
    const result = await apiRequest<{ segments: Segment[] }>(
      `/projects/${projectId}/transcript/segments/${segment.id}/merge`,
      { method: "POST", body: JSON.stringify({ next_segment_id: next.id }) },
      token,
    );
    setSegments(result.segments);
  }

  async function saveTrim(original: AudioAsset) {
    setBusy(true);
    try {
      await apiRequest<AudioAsset>(
        `/projects/${projectId}/audio/${original.id}/trim`,
        {
          method: "PATCH",
          body: JSON.stringify({ start_ms: trim.start, end_ms: trim.end }),
        },
        token,
      );
      setProject(
        (current) => current && { ...current, status: "transcribing" },
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "برش صدا ذخیره نشد.");
    } finally {
      setBusy(false);
    }
  }

  async function generateDraft() {
    setBusy(true);
    try {
      const result = await apiRequest<{ assignments: Assignment[] }>(
        `/projects/${projectId}/draft`,
        { method: "POST", body: "{}" },
        token,
      );
      setAssignments(result.assignments);
      setProject(
        (current) => current && { ...current, current_step: "preview" },
      );
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "پیش‌نویس ساخته نشد.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function assignMedia(segmentId: string, mediaId: string) {
    const updated = await apiRequest<Assignment>(
      `/projects/${projectId}/draft/segments/${segmentId}`,
      { method: "PATCH", body: JSON.stringify({ media_id: mediaId }) },
      token,
    );
    setAssignments((items) => [
      ...items.filter((item) => item.segment_id !== segmentId),
      updated,
    ]);
  }

  async function removeMedia(mediaId: string) {
    if (!window.confirm("این رسانه از پروژه حذف شود؟")) return;
    const result = await apiRequest<{ items: Media[] }>(
      `/projects/${projectId}/media/${mediaId}`,
      { method: "DELETE" },
      token,
    );
    setMedia(result.items);
  }

  async function moveMedia(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= media.length) return;
    const reordered = [...media];
    [reordered[index], reordered[target]] = [
      reordered[target],
      reordered[index],
    ];
    const result = await apiRequest<{ items: Media[] }>(
      `/projects/${projectId}/media/order`,
      {
        method: "PATCH",
        body: JSON.stringify({ media_ids: reordered.map((item) => item.id) }),
      },
      token,
    );
    setMedia(result.items);
  }

  async function replace(mediaId: string, files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    await replaceMedia(token, projectId, mediaId, file);
    await load(token);
  }

  async function exportVideo(tier: "free" | "paid") {
    if (!consent) return setError("پیش از خروجی، تأیید حقوق و رضایت لازم است.");
    setBusy(true);
    try {
      const created = await apiRequest<RenderJob>(
        `/projects/${projectId}/exports`,
        {
          method: "POST",
          headers: { "idempotency-key": crypto.randomUUID() },
          body: JSON.stringify({
            tier,
            owns_media: true,
            owns_voice: true,
            respects_privacy: true,
            no_impersonation: true,
          }),
        },
        token,
      );
      setJob(created);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "درخواست خروجی ثبت نشد.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function download(exportId: string) {
    const result = await apiRequest<{ url: string }>(
      `/projects/${projectId}/exports/${exportId}/download`,
      {},
      token,
    );
    window.location.assign(result.url);
  }

  async function preview(exportId: string) {
    const result = await apiRequest<{ url: string }>(
      `/projects/${projectId}/exports/${exportId}/download`,
      {},
      token,
    );
    setPreviewUrls((items) => ({ ...items, [exportId]: result.url }));
  }

  async function share(exportId: string) {
    const result = await apiRequest<{ url: string }>(
      `/projects/${projectId}/exports/${exportId}/share`,
      { method: "POST", body: "{}" },
      token,
    );
    if (navigator.share) {
      await navigator.share({
        title: project?.title ?? "ویدیوی آواتو",
        url: result.url,
      });
    } else {
      await navigator.clipboard.writeText(result.url);
      setError("پیوند امن خروجی کپی شد.");
    }
  }

  if (!project) {
    return (
      <main className="grid min-h-screen place-items-center">
        <LoaderCircle className="size-8 animate-spin text-[var(--coral)]" />
        <p className="sr-only">در حال بارگذاری پروژه</p>
      </main>
    );
  }

  const processedAudioReady = audio.some((item) => item.kind === "cleaned");
  const projectReadyToRender = processedAudioReady && segments.length > 0;

  return (
    <main className="min-h-screen pb-24">
      <header className="border-b border-black/5 bg-white/50 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
          <Link
            className="flex items-center gap-2 text-sm font-bold"
            href="/projects"
          >
            <ArrowRight className="size-4" /> پروژه‌ها
          </Link>
          <span className="flex items-center gap-2 font-black">
            <span className="grid size-9 place-items-center rounded-xl bg-[var(--ink)] text-white">
              <Mic2 className="size-4" />
            </span>
            آواتو
          </span>
          <span className="rounded-full bg-white px-3 py-1.5 text-xs font-bold">
            {project.status === "ready"
              ? "آماده"
              : project.status === "failed"
                ? "ناموفق"
                : "در حال ویرایش"}
          </span>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-5 pt-8 sm:px-8 lg:grid-cols-[1.1fr_.9fr]">
        <div className="space-y-6">
          <section className="demo-card">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-bold text-[var(--coral)]">
                  تنظیمات ویدیو
                </p>
                <h1 className="mt-1 text-2xl font-black">
                  {project.title || "پروژهٔ بدون عنوان"}
                </h1>
              </div>
              <Save
                className={`size-5 ${busy ? "animate-pulse text-[var(--coral)]" : "text-emerald-700"}`}
              />
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <label className="text-sm font-bold">
                عنوان
                <input
                  className="mt-2 w-full rounded-2xl border border-black/10 bg-white px-4 py-3"
                  defaultValue={project.title ?? ""}
                  onBlur={(event) =>
                    void saveSettings({ title: event.target.value || null })
                  }
                />
              </label>
              <label className="text-sm font-bold">
                سبک
                <select
                  className="mt-2 w-full rounded-2xl border border-black/10 bg-white px-4 py-3"
                  value={project.template_id}
                  onChange={(event) =>
                    void saveSettings({ template_id: event.target.value })
                  }
                >
                  {templates.map(([id, label]) => (
                    <option value={id} key={id}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm font-bold">
                موسیقی
                <select
                  className="mt-2 w-full rounded-2xl border border-black/10 bg-white px-4 py-3"
                  value={project.music_track_id ?? "none"}
                  onChange={(event) =>
                    void saveSettings({
                      music_track_id:
                        event.target.value === "none"
                          ? null
                          : event.target.value,
                    })
                  }
                >
                  <option value="none">بدون موسیقی</option>
                  <option value="calm-local">آرام</option>
                  <option value="emotional-local">احساسی</option>
                  <option value="upbeat-local">پرانرژی</option>
                </select>
              </label>
              <div className="flex items-end">
                <button
                  className="secondary-button w-full"
                  disabled={busy}
                  onClick={generateDraft}
                >
                  <WandSparkles className="size-4" /> بازسازی پیش‌نویس
                </button>
              </div>
            </div>
          </section>

          <section className="demo-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-[var(--coral)]">
                  زیرنویس هماهنگ
                </p>
                <h2 className="mt-1 text-xl font-black">اصلاح متن</h2>
              </div>
              <button
                className="quiet-button !min-h-9 !px-3 !py-1 text-xs"
                onClick={restoreTranscript}
              >
                <RefreshCw className="size-3.5" /> بازگردانی متن اصلی
              </button>
            </div>
            {segments.length === 0 ? (
              <div className="mt-6 rounded-2xl bg-amber-50 p-5 text-sm leading-7 text-amber-900">
                پردازش صدا هنوز کامل نشده است. این صفحه را کمی بعد تازه کنید.
              </div>
            ) : (
              <div className="mt-5 space-y-3">
                {segments.map((segment, index) => (
                  <div
                    className="rounded-2xl border border-black/5 bg-white/70 p-4"
                    key={segment.id}
                  >
                    <div className="mb-2 flex items-center justify-between gap-2 text-[11px] text-[var(--muted-ink)]">
                      <span>بخش {segment.position + 1}</span>
                      <span className="flex items-center gap-3">
                        {segment.text.length >= 4 && (
                          <button
                            className="font-bold"
                            onClick={() => void splitTranscript(segment)}
                          >
                            جداکردن
                          </button>
                        )}
                        {segments[index + 1] && (
                          <button
                            className="font-bold"
                            onClick={() =>
                              void mergeTranscript(segment, segments[index + 1])
                            }
                          >
                            ادغام با بعدی
                          </button>
                        )}
                        <button
                          className="inline-flex items-center gap-1 font-bold text-[var(--coral)]"
                          onClick={() =>
                            void saveSegment({
                              ...segment,
                              text: segment.text.trim(),
                            })
                          }
                        >
                          <Check className="size-3" /> ذخیره
                        </button>
                      </span>
                    </div>
                    <textarea
                      className="min-h-16 w-full resize-y bg-transparent leading-8 outline-none"
                      value={segment.text}
                      onChange={(event) =>
                        setSegments((items) =>
                          items.map((item) =>
                            item.id === segment.id
                              ? { ...item, text: event.target.value }
                              : item,
                          ),
                        )
                      }
                    />
                    <div className="mt-2 flex flex-wrap items-center gap-1">
                      {segment.words
                        .filter((word) => word.confidence < 0.72)
                        .map((word) => (
                          <span
                            className="rounded-lg bg-amber-100 px-2 py-1 text-[11px] font-bold text-amber-900"
                            title={`اطمینان ${Math.round(word.confidence * 100)}٪`}
                            key={word.id}
                          >
                            {word.text}؟
                          </span>
                        ))}
                      {media.length > 0 && (
                        <select
                          className="mr-auto rounded-lg border border-black/10 bg-white px-2 py-1 text-[11px]"
                          aria-label={`رسانه بخش ${segment.position + 1}`}
                          value={
                            assignments.find(
                              (item) => item.segment_id === segment.id,
                            )?.media_id ?? ""
                          }
                          onChange={(event) =>
                            void assignMedia(segment.id, event.target.value)
                          }
                        >
                          <option value="" disabled>
                            انتخاب تصویر
                          </option>
                          {media.map((item) => (
                            <option value={item.id} key={item.id}>
                              {item.position + 1}. {item.original_filename}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="demo-card">
            <div>
              <p className="text-xs font-bold text-[var(--coral)]">رسانه‌ها</p>
              <h2 className="mt-1 text-xl font-black">ترتیب عکس و کلیپ</h2>
            </div>
            <div className="mt-5 grid grid-cols-3 gap-3 sm:grid-cols-4">
              {media.map((item, index) => (
                <div
                  className="relative aspect-[4/5] overflow-hidden rounded-2xl bg-black/5"
                  key={item.id}
                >
                  {item.kind === "photo" ? (
                    <img
                      className="h-full w-full object-cover"
                      alt={item.original_filename}
                      src={item.url}
                    />
                  ) : (
                    <video
                      className="h-full w-full object-cover"
                      muted
                      src={item.url}
                    />
                  )}
                  <span className="absolute top-2 right-2 grid size-6 place-items-center rounded-full bg-black/65 text-[10px] text-white">
                    {item.position + 1}
                  </span>
                  <button
                    className={`absolute top-2 left-2 grid size-7 place-items-center rounded-lg ${project.cover_media_id === item.id ? "bg-amber-300 text-amber-950" : "bg-white/90"}`}
                    onClick={() =>
                      void saveSettings({ cover_media_id: item.id })
                    }
                    aria-label="انتخاب به‌عنوان جلد"
                  >
                    <Star className="size-3.5" />
                  </button>
                  <div className="absolute inset-x-1 bottom-1 flex justify-center gap-1">
                    <button
                      className="grid size-7 place-items-center rounded-lg bg-white/90"
                      disabled={index === 0}
                      onClick={() => void moveMedia(index, -1)}
                      aria-label="انتقال به قبل"
                    >
                      <ChevronRight className="size-3.5" />
                    </button>
                    <label
                      className="grid size-7 cursor-pointer place-items-center rounded-lg bg-white/90"
                      aria-label="جایگزینی رسانه"
                    >
                      <Upload className="size-3.5" />
                      <input
                        className="sr-only"
                        type="file"
                        accept="image/*,video/*"
                        onChange={(event) =>
                          void replace(item.id, event.target.files)
                        }
                      />
                    </label>
                    <button
                      className="grid size-7 place-items-center rounded-lg bg-white/90 text-red-700"
                      onClick={() => void removeMedia(item.id)}
                      aria-label="حذف رسانه"
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                    <button
                      className="grid size-7 place-items-center rounded-lg bg-white/90"
                      disabled={index === media.length - 1}
                      onClick={() => void moveMedia(index, 1)}
                      aria-label="انتقال به بعد"
                    >
                      <ChevronLeft className="size-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <aside className="space-y-6 lg:sticky lg:top-6 lg:self-start">
          <section className="demo-card">
            <div className="phone-frame mx-auto !w-full max-w-[255px]">
              <div className="relative flex h-full flex-col overflow-hidden rounded-[1.55rem] bg-gradient-to-b from-[#496757] to-[#2b2020] p-4 text-white">
                {(media.find((item) => item.id === project.cover_media_id) ??
                media[0]) ? (
                  (
                    media.find((item) => item.id === project.cover_media_id) ??
                    media[0]
                  ).kind === "photo" ? (
                    <img
                      className="absolute inset-0 h-full w-full object-cover opacity-55"
                      alt="پیش‌نمایش"
                      src={
                        (
                          media.find(
                            (item) => item.id === project.cover_media_id,
                          ) ?? media[0]
                        ).url
                      }
                    />
                  ) : (
                    <video
                      className="absolute inset-0 h-full w-full object-cover opacity-55"
                      muted
                      src={
                        (
                          media.find(
                            (item) => item.id === project.cover_media_id,
                          ) ?? media[0]
                        ).url
                      }
                    />
                  )
                ) : (
                  <ImageIcon className="absolute top-1/3 right-1/2 size-12 translate-x-1/2 opacity-50" />
                )}
                <div className="relative z-10 pt-16 text-center text-xl font-black">
                  {project.title || "قصهٔ من"}
                </div>
                <div className="relative z-10 mt-auto mb-14 rounded-2xl bg-black/45 p-3 text-center text-xs leading-6">
                  {segments[0]?.text ||
                    "زیرنویس پس از پردازش اینجا دیده می‌شود"}
                </div>
              </div>
            </div>
            {audio.map((item) => (
              <div className="mt-5" key={item.id}>
                <div className="mb-2 flex items-center gap-2 text-xs font-bold">
                  <Play className="size-3.5" />{" "}
                  {item.kind === "cleaned" ? "صدای پاک‌سازی‌شده" : "صدای اصلی"}
                </div>
                <audio className="w-full" controls src={item.url} />
                {item.kind === "cleaned" && item.analysis.warning && (
                  <p className="mt-2 rounded-xl bg-amber-50 p-3 text-xs leading-6 text-amber-900">
                    کیفیت صدا هنوز ایده‌آل نیست: {item.analysis.warning}. اگر
                    گفتار واضح نیست، دوباره ضبط کنید.
                  </p>
                )}
                {item.kind === "original" && (
                  <div className="mt-3 rounded-2xl bg-black/[.03] p-3">
                    <div className="flex justify-between text-[11px] font-bold">
                      <span>شروع: {(trim.start / 1000).toFixed(1)} ثانیه</span>
                      <span>پایان: {(trim.end / 1000).toFixed(1)} ثانیه</span>
                    </div>
                    <input
                      className="mt-2 w-full accent-[var(--coral)]"
                      type="range"
                      min={0}
                      max={Math.max(0, trim.end - 5000)}
                      step={100}
                      value={trim.start}
                      onChange={(event) =>
                        setTrim((current) => ({
                          ...current,
                          start: Number(event.target.value),
                        }))
                      }
                      aria-label="شروع برش"
                    />
                    <input
                      className="w-full accent-[var(--coral)]"
                      type="range"
                      min={trim.start + 5000}
                      max={Math.min(
                        item.duration_ms,
                        project.duration_limit_seconds * 1000 + trim.start,
                      )}
                      step={100}
                      value={trim.end}
                      onChange={(event) =>
                        setTrim((current) => ({
                          ...current,
                          end: Number(event.target.value),
                        }))
                      }
                      aria-label="پایان برش"
                    />
                    <button
                      className="quiet-button mt-2 !min-h-9 w-full !py-1 text-xs"
                      disabled={busy}
                      onClick={() => void saveTrim(item)}
                    >
                      <Scissors className="size-3.5" /> ذخیرهٔ برش و پردازش
                      دوباره
                    </button>
                  </div>
                )}
              </div>
            ))}
          </section>

          <section className="demo-card">
            <div className="flex items-center gap-3">
              <span className="grid size-10 place-items-center rounded-xl bg-emerald-50 text-emerald-700">
                <ShieldCheck className="size-5" />
              </span>
              <div>
                <h2 className="font-black">خروجی و اشتراک</h2>
                <p className="text-xs text-[var(--muted-ink)]">
                  اعتبار فقط پس از موفقیت کم می‌شود.
                </p>
              </div>
            </div>
            <label className="mt-5 flex cursor-pointer items-start gap-3 rounded-2xl bg-black/[.03] p-4 text-xs leading-6">
              <input
                className="mt-1 size-4 accent-[var(--coral)]"
                type="checkbox"
                checked={consent}
                onChange={(event) => setConsent(event.target.checked)}
              />
              <span>
                تأیید می‌کنم حق استفاده از تصویرها و صدا را دارم، حریم خصوصی
                افراد رعایت شده و از آواتو برای جعل هویت یا فریب استفاده
                نمی‌کنم.
              </span>
            </label>
            {job && (
              <div
                className={`mt-4 rounded-2xl p-4 text-sm ${job.status === "failed" ? "bg-red-50 text-red-800" : job.status === "succeeded" ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-900"}`}
              >
                <div className="flex items-center gap-2">
                  {["queued", "running"].includes(job.status) && (
                    <LoaderCircle className="size-4 animate-spin" />
                  )}
                  {job.status === "succeeded"
                    ? "خروجی آماده شد."
                    : job.status === "failed"
                      ? job.error_detail ||
                        "ساخت خروجی ناموفق بود؛ دوباره تلاش کنید."
                      : `در حال ساخت… ${job.progress}٪`}
                </div>
              </div>
            )}
            <div className="mt-5 grid gap-3">
              <button
                className="secondary-button w-full"
                disabled={busy || !consent || !projectReadyToRender}
                onClick={() => exportVideo("free")}
              >
                <Film className="size-4" /> خروجی رایگان با نشان آواتو
              </button>
              <button
                className="primary-button w-full"
                disabled={busy || !consent || !projectReadyToRender}
                onClick={() => exportVideo("paid")}
              >
                <Sparkles className="size-4" /> خروجی باکیفیت بدون نشان
              </button>
            </div>
            {!projectReadyToRender && (
              <p className="mt-3 rounded-xl bg-amber-50 p-3 text-xs leading-6 text-amber-900">
                پس از آماده‌شدن و شنیدن صدای پاک‌سازی‌شده می‌توانید پیش‌نمایش و
                خروجی بگیرید.
              </p>
            )}
            {exports.length > 0 && (
              <div className="mt-5 border-t border-black/5 pt-4">
                <p className="mb-3 text-xs font-bold">خروجی‌های آماده</p>
                {exports.map((item) => (
                  <div key={item.id}>
                    <div className="mb-2 flex w-full items-center gap-2 rounded-xl bg-emerald-50 p-3 text-xs font-bold text-emerald-800">
                      <span>
                        {item.width}×{item.height} ·{" "}
                        {item.watermarked ? "با نشان" : "بدون نشان"}
                      </span>
                      <button
                        className="mr-auto"
                        onClick={() => void preview(item.id)}
                        aria-label="پخش پیش‌نمایش"
                      >
                        <Play className="size-4" />
                      </button>
                      <button
                        onClick={() => download(item.id)}
                        aria-label="دانلود"
                      >
                        <Download className="size-4" />
                      </button>
                      <button
                        onClick={() => void share(item.id)}
                        aria-label="اشتراک"
                      >
                        <Share2 className="size-4" />
                      </button>
                    </div>
                    {previewUrls[item.id] && (
                      <video
                        className="mb-3 aspect-[9/16] w-full rounded-2xl bg-black"
                        controls
                        src={previewUrls[item.id]}
                      />
                    )}
                  </div>
                ))}
              </div>
            )}
            <Link
              className="mt-4 flex items-center justify-center gap-2 text-xs font-bold text-[var(--coral)]"
              href="/projects"
            >
              <Music2 className="size-4" /> خرید اعتبار از بخش پروژه‌ها
            </Link>
          </section>
          {error && (
            <p
              role="alert"
              className="rounded-2xl bg-red-50 p-4 text-sm leading-7 text-red-800"
            >
              {error}
            </p>
          )}
        </aside>
      </div>
    </main>
  );
}
