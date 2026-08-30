"use client";

/* eslint-disable @next/next/no-img-element -- object URLs are local upload previews. */

import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  ChevronUp,
  CircleStop,
  Film,
  ImagePlus,
  LockKeyhole,
  Mic2,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Trash2,
  Upload,
  WandSparkles,
  X,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import {
  authenticate,
  createProject,
  updateProject,
  uploadAsset,
} from "@/lib/api";

type MediaItem = {
  id: string;
  file: File;
  url: string;
  kind: "photo" | "clip";
};

const steps = ["صدا", "رسانه", "سبک", "بازبینی"];
const templates = [
  {
    id: "clean-story",
    title: "روایت ساده",
    copy: "تمیز و خوانا",
    colors: "from-[#314f43] to-[#b48261]",
  },
  {
    id: "dynamic-voice",
    title: "صدای پویا",
    copy: "درشت و پرانرژی",
    colors: "from-[#432b6d] to-[#de5a3e]",
  },
  {
    id: "memory-film",
    title: "فیلم خاطره",
    copy: "نرم و احساسی",
    colors: "from-[#77584a] to-[#d9bfa2]",
  },
];

export default function StudioPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [duration, setDuration] = useState(30);
  const [audio, setAudio] = useState<{
    blob: Blob;
    url: string;
    name: string;
  } | null>(null);
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [media, setMedia] = useState<MediaItem[]>([]);
  const [template, setTemplate] = useState("clean-story");
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState(
    "اینجا متن فارسیِ هماهنگ با صدای شما دیده می‌شود.",
  );
  const [music, setMusic] = useState("none");
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"register" | "login">("register");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function toggleRecording() {
    if (recording) {
      recorderRef.current?.stop();
      if (timerRef.current) clearInterval(timerRef.current);
      setRecording(false);
      return;
    }
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks: BlobPart[] = [];
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      recorder.ondataavailable = (event) => chunks.push(event.data);
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        if (audio) URL.revokeObjectURL(audio.url);
        setAudio({ blob, url: URL.createObjectURL(blob), name: "ضبط تازه" });
        stream.getTracks().forEach((track) => track.stop());
      };
      recorderRef.current = recorder;
      setElapsed(0);
      recorder.start();
      setRecording(true);
      timerRef.current = setInterval(
        () => setElapsed((value) => value + 1),
        1000,
      );
    } catch {
      setError(
        "اجازهٔ میکروفن داده نشد. می‌توانید فایل صوتی را بارگذاری کنید.",
      );
    }
  }

  function chooseAudio(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    if (!file.type.startsWith("audio/")) {
      setError("لطفاً یک فایل صوتی معتبر انتخاب کنید.");
      return;
    }
    if (audio) URL.revokeObjectURL(audio.url);
    setAudio({ blob: file, url: URL.createObjectURL(file), name: file.name });
    setError("");
  }

  function chooseMedia(files: FileList | null) {
    if (!files) return;
    const incoming = Array.from(files).filter(
      (file) =>
        file.type.startsWith("image/") || file.type.startsWith("video/"),
    );
    if (media.length + incoming.length > 12) {
      setError("حداکثر ۱۲ عکس یا کلیپ می‌توانید انتخاب کنید.");
      return;
    }
    setMedia((items) => [
      ...items,
      ...incoming.map((file) => ({
        id: crypto.randomUUID(),
        file,
        url: URL.createObjectURL(file),
        kind: file.type.startsWith("video/")
          ? ("clip" as const)
          : ("photo" as const),
      })),
    ]);
    setError("");
  }

  function moveMedia(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= media.length) return;
    setMedia((items) => {
      const next = [...items];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  function continueFlow() {
    if (step === 0 && !audio)
      return setError("اول یک ویس ضبط یا بارگذاری کنید.");
    if (step === 1 && media.length < 1)
      return setError("حداقل یک عکس یا کلیپ لازم است.");
    setError("");
    setStep((value) => Math.min(3, value + 1));
  }

  async function saveProject() {
    const existingToken = window.sessionStorage.getItem("avato_token");
    if (!existingToken) return setAuthOpen(true);
    await persist(existingToken);
  }

  async function persist(token: string) {
    setBusy(true);
    setError("");
    try {
      const project = await createProject(token, title, duration);
      if (!audio) throw new Error("فایل صوتی پیدا نشد.");
      await uploadAsset(token, project.id, "audio", audio.blob, audio.name);
      for (const item of media) {
        await uploadAsset(
          token,
          project.id,
          "media",
          item.file,
          item.file.name,
        );
      }
      await updateProject(token, project.id, {
        template_id: template,
        music_track_id: music === "none" ? null : music,
        title: title || null,
        current_step: "preview",
      });
      setSaved(true);
      router.push(`/projects/${project.id}`);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "ذخیرهٔ پروژه انجام نشد.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function submitAuth(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const token = await authenticate(authMode, email, password);
      window.sessionStorage.setItem("avato_token", token);
      setAuthOpen(false);
      await persist(token);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "ورود انجام نشد.");
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen pb-20">
      <header className="border-b border-black/5 bg-white/45 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
          <Link className="flex items-center gap-2 font-black" href="/">
            <span className="grid size-9 place-items-center rounded-xl bg-[var(--ink)] text-white">
              <Mic2 className="size-4" />
            </span>
            آواتو
          </Link>
          <div className="flex items-center gap-2 text-xs text-[var(--muted-ink)]">
            <ShieldCheck className="size-4 text-emerald-700" /> ذخیرهٔ خصوصی تا
            ۳۰ روز
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-5 pt-8 sm:px-8">
        <ol className="mb-9 grid grid-cols-4 gap-2" aria-label="مراحل ساخت">
          {steps.map((label, index) => (
            <li className="text-center" key={label}>
              <button
                className={`mb-2 h-1.5 w-full rounded-full ${index <= step ? "bg-[var(--coral)]" : "bg-black/10"}`}
                onClick={() => index < step && setStep(index)}
                aria-label={`رفتن به مرحله ${label}`}
              />
              <span
                className={`text-xs font-bold ${index === step ? "text-[var(--ink)]" : "text-[var(--muted-ink)]"}`}
              >
                {label}
              </span>
            </li>
          ))}
        </ol>

        <section className="demo-card !p-5 sm:!p-8">
          {step === 0 && (
            <div className="mx-auto max-w-2xl">
              <div className="mb-7 text-center">
                <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-red-50 text-[var(--coral)]">
                  <Mic2 />
                </span>
                <h1 className="mt-4 text-2xl font-black">
                  قصه‌ات را با صدای خودت بگو
                </h1>
                <p className="mt-2 text-sm leading-7 text-[var(--muted-ink)]">
                  ۵ تا {duration} ثانیه، طبیعی و بدون عجله. صدای شما عوض یا
                  بازسازی نمی‌شود.
                </p>
              </div>
              <div className="mb-5 flex justify-center gap-2">
                {[15, 30, 60].map((value) => (
                  <button
                    className={`rounded-xl px-4 py-2 text-sm font-bold ${duration === value ? "bg-[var(--ink)] text-white" : "bg-black/5"}`}
                    key={value}
                    onClick={() => setDuration(value)}
                  >
                    {value} ثانیه
                  </button>
                ))}
              </div>
              <div className="rounded-3xl border border-dashed border-black/15 bg-[#fffaf4] p-6 text-center">
                {audio ? (
                  <div>
                    <p className="mb-3 text-sm font-bold">{audio.name}</p>
                    <audio
                      className="mx-auto w-full max-w-md"
                      controls
                      src={audio.url}
                    />
                    <button
                      className="mt-4 inline-flex items-center gap-2 text-xs font-bold text-[var(--coral)]"
                      onClick={() => setAudio(null)}
                    >
                      <RotateCcw className="size-4" /> انتخاب دوباره
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      className={`mx-auto grid size-20 place-items-center rounded-full text-white shadow-xl ${recording ? "animate-pulse bg-red-700" : "bg-[var(--coral)]"}`}
                      onClick={toggleRecording}
                      aria-label={recording ? "پایان ضبط" : "شروع ضبط"}
                    >
                      {recording ? <CircleStop /> : <Mic2 />}
                    </button>
                    <p className="mt-4 text-sm font-bold">
                      {recording
                        ? `در حال ضبط · ${elapsed} ثانیه`
                        : "برای ضبط لمس کنید"}
                    </p>
                    <div className="my-5 flex items-center gap-3 text-xs text-[var(--muted-ink)]">
                      <i className="h-px flex-1 bg-black/10" /> یا{" "}
                      <i className="h-px flex-1 bg-black/10" />
                    </div>
                    <label className="secondary-button cursor-pointer">
                      <Upload className="size-4" /> بارگذاری فایل صوتی
                      <input
                        className="sr-only"
                        type="file"
                        accept="audio/*"
                        onChange={(event) => chooseAudio(event.target.files)}
                      />
                    </label>
                  </>
                )}
              </div>
              <div className="mt-5 flex gap-3 rounded-2xl bg-emerald-50 p-4 text-xs leading-6 text-emerald-900">
                <LockKeyhole className="mt-1 size-4 shrink-0" />
                <p>
                  فایل‌ها فقط برای ساخت ویدیوی درخواستی شما استفاده می‌شوند؛
                  فروخته یا عمومی نمی‌شوند و بدون رضایت جداگانه برای آموزش
                  قابلیت‌های عمومی به کار نمی‌روند. بازبین انسانی به فایل‌ها
                  دسترسی ندارد، مگر برای پشتیبانی با اجازهٔ روشن شما.
                </p>
              </div>
            </div>
          )}

          {step === 1 && (
            <div>
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
                <div>
                  <h1 className="text-2xl font-black">
                    عکس‌ها و کلیپ‌ها را اضافه کن
                  </h1>
                  <p className="mt-2 text-sm text-[var(--muted-ink)]">
                    برای {duration} ثانیه،{" "}
                    {duration === 15
                      ? "۲ تا ۴"
                      : duration === 30
                        ? "۵ تا ۸"
                        : "۸ تا ۱۲"}{" "}
                    مورد معمولاً بهترین نتیجه را می‌دهد.
                  </p>
                </div>
                <label className="primary-button cursor-pointer">
                  <ImagePlus className="size-4" /> افزودن رسانه
                  <input
                    className="sr-only"
                    type="file"
                    accept="image/*,video/*"
                    multiple
                    onChange={(event) => chooseMedia(event.target.files)}
                  />
                </label>
              </div>
              {media.length === 0 ? (
                <label className="mt-7 grid min-h-64 cursor-pointer place-items-center rounded-3xl border border-dashed border-black/15 bg-[#fffaf4] text-center">
                  <span>
                    <ImagePlus className="mx-auto mb-3 size-8 text-[var(--coral)]" />
                    <b className="block">عکس یا کلیپ انتخاب کنید</b>
                    <small className="mt-2 block text-[var(--muted-ink)]">
                      حداقل ۱ و حداکثر ۱۲ مورد
                    </small>
                  </span>
                  <input
                    className="sr-only"
                    type="file"
                    accept="image/*,video/*"
                    multiple
                    onChange={(event) => chooseMedia(event.target.files)}
                  />
                </label>
              ) : (
                <div className="mt-7 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
                  {media.map((item, index) => (
                    <div
                      className="group relative overflow-hidden rounded-2xl bg-black/5"
                      key={item.id}
                    >
                      <div className="aspect-[4/5]">
                        {item.kind === "photo" ? (
                          <img
                            className="h-full w-full object-cover"
                            alt={`رسانه ${index + 1}`}
                            src={item.url}
                          />
                        ) : (
                          <video
                            className="h-full w-full object-cover"
                            muted
                            src={item.url}
                          />
                        )}
                      </div>
                      <span className="absolute top-2 right-2 grid size-7 place-items-center rounded-full bg-black/65 text-xs text-white">
                        {index + 1}
                      </span>
                      <div className="absolute inset-x-2 bottom-2 flex justify-center gap-1">
                        <button
                          className="grid size-8 place-items-center rounded-lg bg-white/90"
                          onClick={() => moveMedia(index, -1)}
                          disabled={index === 0}
                        >
                          <ChevronUp className="size-4" />
                        </button>
                        <button
                          className="grid size-8 place-items-center rounded-lg bg-white/90 text-red-700"
                          onClick={() => {
                            URL.revokeObjectURL(item.url);
                            setMedia((items) =>
                              items.filter((entry) => entry.id !== item.id),
                            );
                          }}
                        >
                          <Trash2 className="size-4" />
                        </button>
                        <button
                          className="grid size-8 place-items-center rounded-lg bg-white/90"
                          onClick={() => moveMedia(index, 1)}
                          disabled={index === media.length - 1}
                        >
                          <ChevronDown className="size-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {step === 2 && (
            <div>
              <h1 className="text-2xl font-black">
                حال‌وهوای ویدیو را انتخاب کن
              </h1>
              <p className="mt-2 text-sm text-[var(--muted-ink)]">
                هر سبک حرکت، گذار و زیرنویس مخصوص خودش را دارد.
              </p>
              <div className="mt-7 grid gap-4 sm:grid-cols-3">
                {templates.map((item) => (
                  <button
                    className={`overflow-hidden rounded-3xl border-2 text-right transition ${template === item.id ? "border-[var(--coral)] shadow-lg" : "border-transparent bg-black/5"}`}
                    key={item.id}
                    onClick={() => setTemplate(item.id)}
                  >
                    <div
                      className={`relative aspect-[9/12] bg-gradient-to-b ${item.colors} p-4 text-white`}
                    >
                      <div className="absolute inset-x-5 bottom-8 rounded-xl bg-black/35 p-2 text-center text-xs">
                        این یک نمونه زیرنویس است
                      </div>
                      {template === item.id && (
                        <span className="absolute top-3 left-3 grid size-7 place-items-center rounded-full bg-white text-[var(--coral)]">
                          <Check className="size-4" />
                        </span>
                      )}
                    </div>
                    <div className="bg-white p-4">
                      <b>{item.title}</b>
                      <small className="mt-1 block text-[var(--muted-ink)]">
                        {item.copy}
                      </small>
                    </div>
                  </button>
                ))}
              </div>
              <div className="mt-7 grid gap-5 sm:grid-cols-2">
                <label className="text-sm font-bold">
                  عنوان اختیاری
                  <input
                    className="mt-2 w-full rounded-2xl border border-black/10 bg-white px-4 py-3 outline-none focus:border-[var(--coral)]"
                    maxLength={120}
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    placeholder="مثلاً: سفر شمال"
                  />
                </label>
                <label className="text-sm font-bold">
                  موسیقی
                  <select
                    className="mt-2 w-full rounded-2xl border border-black/10 bg-white px-4 py-3"
                    value={music}
                    onChange={(event) => setMusic(event.target.value)}
                  >
                    <option value="none">بدون موسیقی</option>
                    <option value="calm-local">آرام</option>
                    <option value="emotional-local">احساسی</option>
                    <option value="upbeat-local">پرانرژی</option>
                  </select>
                </label>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="grid gap-8 lg:grid-cols-[.8fr_1.2fr]">
              <div className="phone-frame mx-auto !w-full max-w-[260px]">
                <div
                  className={`relative flex h-full flex-col overflow-hidden rounded-[1.55rem] bg-gradient-to-b ${templates.find((item) => item.id === template)?.colors} p-4 text-white`}
                >
                  {media[0] &&
                    (media[0].kind === "photo" ? (
                      <img
                        className="absolute inset-0 h-full w-full object-cover opacity-55"
                        alt="کاور"
                        src={media[0].url}
                      />
                    ) : (
                      <video
                        className="absolute inset-0 h-full w-full object-cover opacity-55"
                        muted
                        src={media[0].url}
                      />
                    ))}
                  <div className="relative z-10 pt-16 text-center">
                    <p className="text-2xl font-black">{title || "قصهٔ من"}</p>
                  </div>
                  <div className="relative z-10 mt-auto mb-16 rounded-2xl bg-black/45 p-3 text-center text-sm leading-7 backdrop-blur">
                    {subtitle}
                  </div>
                  {template === "dynamic-voice" && (
                    <div className="relative z-10 mb-4 flex h-5 items-center justify-center gap-1">
                      {[8, 15, 5, 18, 10, 14, 6, 17].map((height, index) => (
                        <i
                          className="w-1 rounded bg-amber-300"
                          style={{ height }}
                          key={index}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div>
                <div className="eyebrow">
                  <WandSparkles className="size-4" /> آمادهٔ ساخت پیش‌نمایش
                </div>
                <h1 className="mt-4 text-2xl font-black">
                  قبل از خروجی، همه‌چیز قابل اصلاح است
                </h1>
                <p className="mt-2 text-sm leading-7 text-[var(--muted-ink)]">
                  آواتو تغییر تصویرها را کنار مرز جمله‌ها می‌چیند. کلیپ‌ها
                  بی‌صدا می‌شوند تا روایت شما واضح بماند.
                </p>
                <label className="mt-6 block text-sm font-bold">
                  متن زیرنویس
                  <textarea
                    className="mt-2 min-h-28 w-full resize-y rounded-2xl border border-black/10 bg-white p-4 leading-7"
                    value={subtitle}
                    onChange={(event) => setSubtitle(event.target.value)}
                  />
                </label>
                <div className="mt-4 flex items-center gap-2 rounded-2xl bg-amber-50 p-4 text-xs leading-6 text-amber-900">
                  <Sparkles className="size-4 shrink-0" /> واژه‌هایی که تشخیص
                  آن‌ها مطمئن نباشد، برای بازشنوی و اصلاح مشخص می‌شوند.
                </div>
                {media.length < 3 && (
                  <p className="mt-3 rounded-2xl bg-violet-50 p-4 text-xs leading-6 text-violet-900">
                    با این تعداد تصویر ممکن است بعضی نماها تکرار شوند. سبک «صدای
                    پویا» برای رسانهٔ کم مناسب‌تر است.
                  </p>
                )}
                <button
                  className="primary-button mt-6 w-full"
                  disabled={busy || saved}
                  onClick={saveProject}
                >
                  {saved ? (
                    <>
                      <Check className="size-5" /> پروژه ذخیره شد
                    </>
                  ) : busy ? (
                    "در حال ذخیره…"
                  ) : (
                    <>
                      <Film className="size-5" /> ذخیره و ساخت پیش‌نمایش
                    </>
                  )}
                </button>
                <p className="mt-3 text-center text-xs text-[var(--muted-ink)]">
                  برای ذخیره، خروجی یا پرداخت به حساب نیاز دارید.
                </p>
              </div>
            </div>
          )}

          {error && (
            <div
              role="alert"
              className="mt-6 flex items-center justify-between rounded-2xl bg-red-50 p-4 text-sm text-red-800"
            >
              <span>{error}</span>
              <button onClick={() => setError("")}>
                <X className="size-4" />
              </button>
            </div>
          )}
          <div className="mt-8 flex items-center justify-between border-t border-black/5 pt-6">
            <button
              className="quiet-button disabled:opacity-40"
              disabled={step === 0}
              onClick={() => setStep((value) => value - 1)}
            >
              <ArrowRight className="size-4" /> قبلی
            </button>
            {step < 3 && (
              <button className="primary-button" onClick={continueFlow}>
                ادامه <ArrowLeft className="size-4" />
              </button>
            )}
          </div>
        </section>
      </div>

      {authOpen && (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-black/45 p-5 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="auth-title"
        >
          <form
            className="w-full max-w-md rounded-3xl bg-[var(--paper)] p-6 shadow-2xl"
            onSubmit={submitAuth}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-bold text-[var(--coral)]">
                  پروژه‌ات آمادهٔ ذخیره است
                </p>
                <h2 className="mt-1 text-xl font-black" id="auth-title">
                  {authMode === "register"
                    ? "ساخت حساب آواتو"
                    : "ورود به آواتو"}
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setAuthOpen(false)}
                aria-label="بستن"
              >
                <X />
              </button>
            </div>
            <p className="mt-3 text-sm leading-7 text-[var(--muted-ink)]">
              فایل‌های انتخابی تا پیش از ذخیره روی همین دستگاه می‌مانند.
            </p>
            <label className="mt-5 block text-sm font-bold">
              ایمیل
              <input
                className="mt-2 w-full rounded-2xl border border-black/10 bg-white px-4 py-3"
                dir="ltr"
                required
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <label className="mt-4 block text-sm font-bold">
              رمز عبور
              <input
                className="mt-2 w-full rounded-2xl border border-black/10 bg-white px-4 py-3"
                dir="ltr"
                minLength={8}
                required
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            <button className="primary-button mt-6 w-full" disabled={busy}>
              {busy
                ? "کمی صبر کنید…"
                : authMode === "register"
                  ? "ساخت حساب و ادامه"
                  : "ورود و ادامه"}
            </button>
            <button
              className="mx-auto mt-4 block text-xs font-bold text-[var(--coral)]"
              type="button"
              onClick={() =>
                setAuthMode((value) =>
                  value === "register" ? "login" : "register",
                )
              }
            >
              {authMode === "register"
                ? "حساب دارم؛ وارد می‌شوم"
                : "حساب ندارم؛ ثبت‌نام می‌کنم"}
            </button>
          </form>
        </div>
      )}
    </main>
  );
}
