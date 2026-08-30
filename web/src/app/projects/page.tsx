"use client";

import {
  CalendarClock,
  Coins,
  Film,
  LogIn,
  Mic2,
  Plus,
  Trash2,
  UserX,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import {
  apiRequest,
  authenticate,
  deleteProject,
  listProjects,
  type Project,
} from "@/lib/api";

const statusFa: Record<string, string> = {
  draft: "پیش‌نویس",
  transcribing: "در حال تبدیل صدا",
  editing: "قابل ویرایش",
  rendering: "در حال ساخت",
  ready: "آماده",
  failed: "نیازمند تلاش دوباره",
  cancelled: "لغوشده",
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [token, setToken] = useState(() =>
    typeof window === "undefined"
      ? ""
      : (window.sessionStorage.getItem("avato_token") ?? ""),
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [now] = useState(() => Date.now());

  useEffect(() => {
    if (!token) {
      queueMicrotask(() => setLoading(false));
      return;
    }
    const timer = window.setTimeout(async () => {
      setLoading(true);
      try {
        setProjects((await listProjects(token)).items);
      } catch (caught) {
        setError(
          caught instanceof Error ? caught.message : "پروژه‌ها بارگذاری نشدند.",
        );
      } finally {
        setLoading(false);
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, [token]);

  async function login(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const authToken = await authenticate("login", email, password);
      window.sessionStorage.setItem("avato_token", authToken);
      setToken(authToken);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "ورود انجام نشد.");
    }
  }

  async function remove(projectId: string) {
    if (
      !window.confirm("این پروژه و همهٔ فایل‌های خصوصی آن برای همیشه پاک شود؟")
    )
      return;
    await deleteProject(token, projectId);
    setProjects((items) => items.filter((item) => item.id !== projectId));
  }

  async function removeAccount() {
    if (
      !window.confirm(
        "حساب، همهٔ پروژه‌ها و فایل‌های خصوصی برای همیشه پاک شوند؟",
      )
    )
      return;
    await apiRequest<{ deleted: boolean }>(
      "/auth/account",
      { method: "DELETE" },
      token,
    );
    window.sessionStorage.removeItem("avato_token");
    setToken("");
    setProjects([]);
  }

  if (!token && !loading) {
    return (
      <main className="grid min-h-screen place-items-center p-5">
        <form className="demo-card w-full max-w-md" onSubmit={login}>
          <span className="grid size-12 place-items-center rounded-2xl bg-[var(--ink)] text-white">
            <LogIn />
          </span>
          <h1 className="mt-5 text-2xl font-black">ورود به پروژه‌های من</h1>
          <p className="mt-2 text-sm leading-7 text-[var(--muted-ink)]">
            پروژه‌ها خصوصی‌اند و فقط با حساب خودتان دیده می‌شوند.
          </p>
          <label className="mt-6 block text-sm font-bold">
            ایمیل
            <input
              className="mt-2 w-full rounded-2xl border border-black/10 bg-white px-4 py-3"
              dir="ltr"
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label className="mt-4 block text-sm font-bold">
            رمز عبور
            <input
              className="mt-2 w-full rounded-2xl border border-black/10 bg-white px-4 py-3"
              dir="ltr"
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error && (
            <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-800">
              {error}
            </p>
          )}
          <button className="primary-button mt-6 w-full">ورود</button>
          <Link
            className="mt-4 block text-center text-xs font-bold text-[var(--coral)]"
            href="/studio"
          >
            ساخت حساب با اولین پروژه
          </Link>
        </form>
      </main>
    );
  }

  return (
    <main className="min-h-screen pb-20">
      <header className="border-b border-black/5 bg-white/45">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
          <Link className="flex items-center gap-2 font-black" href="/">
            <span className="grid size-9 place-items-center rounded-xl bg-[var(--ink)] text-white">
              <Mic2 className="size-4" />
            </span>
            آواتو
          </Link>
          <div className="flex items-center gap-2">
            <Link
              className="quiet-button !min-h-10 !px-3 !py-2"
              href="/credits"
            >
              <Coins className="size-4" /> اعتبار
            </Link>
            <Link
              className="primary-button !min-h-10 !px-4 !py-2"
              href="/studio"
            >
              <Plus className="size-4" /> پروژهٔ تازه
            </Link>
          </div>
        </div>
      </header>
      <section className="mx-auto max-w-6xl px-5 pt-10 sm:px-8">
        <div>
          <p className="text-sm font-bold text-[var(--coral)]">آرشیو ۳۰ روزه</p>
          <h1 className="mt-1 text-3xl font-black">پروژه‌های من</h1>
          <p className="mt-2 text-sm text-[var(--muted-ink)]">
            فایل‌ها ۳۰ روز پس از آخرین فعالیت خودکار پاک می‌شوند.
          </p>
        </div>
        {loading ? (
          <div className="mt-10 animate-pulse rounded-3xl bg-white/60 p-10 text-center text-sm">
            در حال بارگذاری…
          </div>
        ) : projects.length === 0 ? (
          <div className="demo-card mt-10 text-center">
            <Film className="mx-auto size-10 text-[var(--coral)]" />
            <h2 className="mt-4 text-xl font-black">هنوز پروژه‌ای نداری</h2>
            <p className="mt-2 text-sm text-[var(--muted-ink)]">
              اولین قصه را با یک ویس و یک عکس شروع کن.
            </p>
            <Link className="primary-button mt-6" href="/studio">
              شروع ساخت
            </Link>
          </div>
        ) : (
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => {
              const days = Math.max(
                0,
                Math.ceil(
                  (new Date(project.expires_at).getTime() - now) / 86_400_000,
                ),
              );
              return (
                <article
                  className="rounded-3xl border border-black/5 bg-white/75 p-5 shadow-sm"
                  key={project.id}
                >
                  <div className="flex items-start justify-between">
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-bold ${project.status === "ready" ? "bg-emerald-50 text-emerald-700" : project.status === "failed" ? "bg-red-50 text-red-700" : "bg-amber-50 text-amber-800"}`}
                    >
                      {statusFa[project.status] ?? project.status}
                    </span>
                    <button
                      className="grid size-8 place-items-center rounded-xl text-red-700 hover:bg-red-50"
                      aria-label="حذف پروژه"
                      onClick={() => remove(project.id)}
                    >
                      <Trash2 className="size-4" />
                    </button>
                  </div>
                  <h2 className="mt-5 text-lg font-black">
                    {project.title || "پروژهٔ بدون عنوان"}
                  </h2>
                  <p className="mt-1 text-xs text-[var(--muted-ink)]">
                    تا {project.duration_limit_seconds} ثانیه ·{" "}
                    {new Date(project.updated_at).toLocaleDateString("fa-IR")}
                  </p>
                  <div
                    className={`mt-5 flex items-center gap-2 rounded-xl p-3 text-xs ${days <= 3 ? "bg-red-50 text-red-800" : "bg-black/[.03] text-[var(--muted-ink)]"}`}
                  >
                    <CalendarClock className="size-4" />{" "}
                    {days <= 3
                      ? `${days} روز تا حذف خودکار`
                      : `${days} روز از نگهداری باقی مانده`}
                  </div>
                  <Link
                    className="secondary-button mt-4 w-full"
                    href={`/projects/${project.id}`}
                  >
                    ادامه و بازبینی
                  </Link>
                </article>
              );
            })}
          </div>
        )}
        {error && (
          <p className="mt-6 rounded-2xl bg-red-50 p-4 text-sm text-red-800">
            {error}
          </p>
        )}
        {!loading && (
          <div className="mt-12 border-t border-black/5 pt-6 text-left">
            <button
              className="inline-flex items-center gap-2 text-xs font-bold text-red-700"
              onClick={() => void removeAccount()}
            >
              <UserX className="size-4" /> حذف حساب و همهٔ داده‌ها
            </button>
          </div>
        )}
      </section>
    </main>
  );
}
