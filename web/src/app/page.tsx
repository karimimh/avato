import {
  ArrowLeft,
  Check,
  Image as ImageIcon,
  LockKeyhole,
  Mic2,
  Play,
  Sparkles,
  WandSparkles,
} from "lucide-react";
import Link from "next/link";

const features = [
  "زیرنویس فارسی هماهنگ و قابل ویرایش",
  "زمان‌بندی خودکار عکس‌ها با جمله‌های شما",
  "سه سبک آماده برای قصه، نظر و خاطره",
];

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
        <Link className="flex items-center gap-2" href="/">
          <span className="grid size-10 place-items-center rounded-2xl bg-[var(--ink)] text-white shadow-lg shadow-orange-950/10">
            <Mic2 className="size-5" />
          </span>
          <span className="text-xl font-black">آواتو</span>
        </Link>
        <Link className="quiet-button" href="/studio">
          ورود
        </Link>
      </nav>

      <section className="relative mx-auto grid max-w-7xl items-center gap-14 px-5 pt-12 pb-24 sm:px-8 lg:grid-cols-[1.05fr_.95fr] lg:pt-20">
        <div className="relative z-10 max-w-2xl">
          <div className="eyebrow">
            <Sparkles className="size-4" />
            اولین ویدیو رایگان
          </div>
          <h1 className="mt-6 text-[clamp(2.8rem,7vw,6.3rem)] leading-[1.15] font-black text-balance">
            صدات را بگو؛
            <span className="block text-[var(--coral)]">قصه‌اش را ببین.</span>
          </h1>
          <p className="mt-7 max-w-xl text-lg leading-9 text-[var(--muted-ink)] sm:text-xl">
            یک ویس فارسی و چند عکس انتخاب کن. آواتو آن‌ها را به یک ویدیوی عمودیِ
            زیرنویس‌دار و آمادهٔ اشتراک تبدیل می‌کند—بدون ادیت حرفه‌ای.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Link className="primary-button" href="/studio">
              ساخت اولین ریلز
              <ArrowLeft className="size-5" />
            </Link>
            <a className="secondary-button" href="#demo">
              <Play className="size-4 fill-current" />
              دیدن نمونه
            </a>
          </div>
          <ul className="mt-9 grid gap-3 text-sm text-[var(--muted-ink)] sm:grid-cols-2">
            {features.map((feature) => (
              <li className="flex items-center gap-2" key={feature}>
                <span className="grid size-5 place-items-center rounded-full bg-emerald-100 text-emerald-700">
                  <Check className="size-3.5" />
                </span>
                {feature}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative mx-auto w-full max-w-[550px]" id="demo">
          <div className="absolute -top-10 -right-16 size-64 rounded-full bg-[var(--sun)]/25 blur-3xl" />
          <div className="absolute -bottom-10 -left-16 size-72 rounded-full bg-[var(--coral)]/15 blur-3xl" />
          <div className="demo-card relative">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm font-bold">از ویس و عکس تا ریلز</p>
                <p className="mt-1 text-xs text-[var(--muted-ink)]">
                  پیش‌نویس خودکار در چند قدم کوتاه
                </p>
              </div>
              <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700">
                آماده
              </span>
            </div>
            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
              <div className="space-y-3">
                <div className="rounded-3xl border border-black/5 bg-[#fffaf4] p-4">
                  <div className="mb-3 flex items-center gap-2 text-xs font-bold">
                    <Mic2 className="size-4 text-[var(--coral)]" /> ویس ۲۵
                    ثانیه‌ای
                  </div>
                  <div
                    className="flex h-7 items-center gap-1"
                    aria-hidden="true"
                  >
                    {[12, 19, 9, 25, 16, 28, 10, 21, 14, 24, 8, 17].map(
                      (height, index) => (
                        <i
                          className="w-1 rounded-full bg-[var(--coral)]/70"
                          key={index}
                          style={{ height }}
                        />
                      ),
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {["bg-[#ef9f79]", "bg-[#647a6a]", "bg-[#dfc6a5]"].map(
                    (color, index) => (
                      <div
                        className={`aspect-square rounded-2xl ${color}`}
                        key={color}
                      >
                        <span className="grid h-full place-items-center text-white/80">
                          <ImageIcon className="size-5" />
                          <span className="sr-only">عکس {index + 1}</span>
                        </span>
                      </div>
                    ),
                  )}
                </div>
              </div>
              <WandSparkles className="size-5 text-[var(--coral)]" />
              <div className="phone-frame">
                <div className="relative flex h-full flex-col justify-end overflow-hidden rounded-[1.55rem] bg-gradient-to-b from-[#5f7d6b] via-[#9b725a] to-[#231b1a] p-3 text-white">
                  <div className="absolute top-5 right-1/2 h-1.5 w-12 translate-x-1/2 rounded-full bg-black/30" />
                  <div className="mb-auto pt-12 text-center">
                    <p className="text-[9px] opacity-70">برای خواهر خوبم</p>
                    <p className="mt-1 text-base font-black">تولدت مبارک</p>
                  </div>
                  <div className="mb-6 rounded-xl bg-black/35 px-2 py-2 text-center text-[10px] leading-5 backdrop-blur-sm">
                    امیدوارم امسال پر از <mark>خاطره‌های خوب</mark> باشه
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-5 flex items-center justify-center gap-2 text-xs text-[var(--muted-ink)]">
            <LockKeyhole className="size-4" /> پروژه‌های شما خصوصی‌اند و پس از
            ۳۰ روز پاک می‌شوند.
          </div>
        </div>
      </section>

      <section
        className="border-y border-black/5 bg-white/55 py-7 backdrop-blur"
        aria-label="مراحل ساخت"
      >
        <div className="mx-auto grid max-w-5xl gap-6 px-5 sm:grid-cols-3">
          {[
            ["۱", "ویس را ضبط کن", "طبیعی حرف بزن؛ صدایت عوض نمی‌شود."],
            ["۲", "عکس‌ها را بچین", "یک تا دوازده عکس یا کلیپ کوتاه."],
            ["۳", "پیش‌نمایش بگیر", "زیرنویس را اصلاح کن و خروجی بگیر."],
          ].map(([number, title, copy]) => (
            <div className="flex gap-4" key={number}>
              <span className="grid size-10 shrink-0 place-items-center rounded-2xl bg-[var(--cream)] font-black text-[var(--coral)]">
                {number}
              </span>
              <div>
                <h2 className="font-extrabold">{title}</h2>
                <p className="mt-1 text-sm leading-6 text-[var(--muted-ink)]">
                  {copy}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
