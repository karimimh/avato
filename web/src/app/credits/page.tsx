"use client";

import {
  ArrowRight,
  Check,
  CreditCard,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { apiRequest } from "@/lib/api";

type Pack = {
  id: string;
  credits: number;
  amount_rials: number;
  name_fa: string;
};

export default function CreditsPage() {
  const [token] = useState(() =>
    typeof window === "undefined"
      ? ""
      : (window.sessionStorage.getItem("avato_token") ?? ""),
  );
  const [packs, setPacks] = useState<Pack[]>([]);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      try {
        setPacks(
          (await apiRequest<{ items: Pack[] }>("/payments/packs")).items,
        );
      } catch (caught) {
        setError(
          caught instanceof Error ? caught.message : "بسته‌ها بارگذاری نشدند.",
        );
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function buy(packId: string) {
    if (!token) return setError("ابتدا از بخش پروژه‌ها وارد حساب شوید.");
    setBusy(packId);
    try {
      const result = await apiRequest<{ payment_url: string }>(
        "/payments/purchases",
        {
          method: "POST",
          headers: { "idempotency-key": crypto.randomUUID() },
          body: JSON.stringify({ pack_id: packId }),
        },
        token,
      );
      window.location.assign(result.payment_url);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "شروع پرداخت انجام نشد.",
      );
      setBusy("");
    }
  }

  return (
    <main className="min-h-screen pb-20">
      <header className="border-b border-black/5 bg-white/45">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
          <Link
            className="flex items-center gap-2 text-sm font-bold"
            href="/projects"
          >
            <ArrowRight className="size-4" /> پروژه‌ها
          </Link>
          <b className="text-lg">اعتبار آواتو</b>
        </div>
      </header>
      <section className="mx-auto max-w-5xl px-5 pt-12 text-center sm:px-8">
        <div className="eyebrow">
          <Sparkles className="size-4" /> پرداخت امن از درگاه ایرانی
        </div>
        <h1 className="mt-5 text-4xl font-black">
          فقط برای خروجی موفق پرداخت کن
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-sm leading-8 text-[var(--muted-ink)]">
          اعتبار زمانی کم می‌شود که ویدیوی باکیفیت و بدون نشان واقعاً آماده شده
          باشد. تلاش ناموفق و خروجی دوبارهٔ همان پروژه در بازهٔ مجاز، اعتبار
          تازه مصرف نمی‌کند.
        </p>
        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {packs.map((pack) => (
            <article
              className={`rounded-3xl border bg-white/75 p-6 text-right shadow-sm ${pack.id === "medium" ? "border-[var(--coral)]" : "border-black/5"}`}
              key={pack.id}
            >
              {pack.id === "medium" && (
                <span className="mb-4 inline-block rounded-full bg-red-50 px-3 py-1 text-[11px] font-bold text-[var(--coral)]">
                  پیشنهاد معمول
                </span>
              )}
              <h2 className="text-lg font-black">{pack.name_fa}</h2>
              <p className="mt-2 text-3xl font-black">
                {pack.amount_rials.toLocaleString("fa-IR")}{" "}
                <small className="text-xs text-[var(--muted-ink)]">ریال</small>
              </p>
              <ul className="mt-5 space-y-2 text-xs leading-6">
                <li className="flex gap-2">
                  <Check className="size-4 text-emerald-700" />{" "}
                  {pack.credits.toLocaleString("fa-IR")} خروجی باکیفیت
                </li>
                <li className="flex gap-2">
                  <Check className="size-4 text-emerald-700" /> بدون نشان آواتو
                </li>
                <li className="flex gap-2">
                  <Check className="size-4 text-emerald-700" /> هر سه سبک
                </li>
              </ul>
              <button
                className="primary-button mt-6 w-full"
                disabled={busy === pack.id}
                onClick={() => buy(pack.id)}
              >
                <CreditCard className="size-4" />{" "}
                {busy === pack.id ? "در حال اتصال…" : "انتخاب بسته"}
              </button>
            </article>
          ))}
        </div>
        <div className="mx-auto mt-8 flex max-w-2xl items-start gap-3 rounded-2xl bg-emerald-50 p-5 text-right text-xs leading-6 text-emerald-900">
          <ShieldCheck className="mt-1 size-5 shrink-0" />
          <p>
            آواتو هیچ شماره کارت یا رمز بانکی دریافت نمی‌کند. در محیط محلی،
            درگاه آزمایشی هیچ پول واقعی جابه‌جا نمی‌کند؛ اتصال تولیدی از قرارداد
            رسمی زرین‌پال استفاده می‌کند.
          </p>
        </div>
        {error && (
          <p className="mx-auto mt-5 max-w-2xl rounded-2xl bg-red-50 p-4 text-sm text-red-800">
            {error}
          </p>
        )}
      </section>
    </main>
  );
}
