import { expect, test } from "@playwright/test";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

function wav(seconds = 6): Buffer {
  const sampleRate = 16_000;
  const samples = sampleRate * seconds;
  const data = Buffer.alloc(samples * 2);
  for (let index = 0; index < samples; index += 1) {
    data.writeInt16LE(
      Math.round(Math.sin((index / sampleRate) * Math.PI * 440) * 5000),
      index * 2,
    );
  }
  const header = Buffer.alloc(44);
  header.write("RIFF", 0);
  header.writeUInt32LE(36 + data.length, 4);
  header.write("WAVEfmt ", 8);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(1, 22);
  header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(sampleRate * 2, 28);
  header.writeUInt16LE(2, 32);
  header.writeUInt16LE(16, 34);
  header.write("data", 36);
  header.writeUInt32LE(data.length, 40);
  return Buffer.concat([header, data]);
}

const png = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

test("a first-time Persian user creates a private project with one voice and photo", async ({
  page,
  request,
}) => {
  const suffix = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const email = `e2e-${suffix}@avato.local`;
  const password = "e2e-password-2026";
  const registration = await request.post("/api/auth/register", {
    data: { email, password },
  });
  expect(registration.status()).toBe(201);
  const { token } = (await registration.json()) as { token: string };

  const fixtureDir = await mkdtemp(join(tmpdir(), "avato-e2e-"));
  const audioPath = join(fixtureDir, "voice.wav");
  const imagePath = join(fixtureDir, "photo.png");
  await Promise.all([writeFile(audioPath, wav()), writeFile(imagePath, png)]);

  await page.goto("/projects");
  await page.getByLabel("ایمیل", { exact: true }).fill(email);
  await page.getByLabel("رمز عبور", { exact: true }).fill(password);
  await page.getByRole("button", { name: "ورود", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "پروژه‌های من" }),
  ).toBeVisible();

  await page.getByRole("link", { name: "پروژهٔ تازه", exact: true }).click();
  await page.getByLabel("بارگذاری فایل صوتی").setInputFiles(audioPath);
  await page.getByRole("button", { name: "ادامه", exact: true }).click();
  await page.getByLabel("افزودن رسانه").setInputFiles(imagePath);
  await page.getByRole("button", { name: "ادامه", exact: true }).click();
  await page.getByRole("button", { name: /صدای پویا/ }).click();
  await page.getByLabel("عنوان اختیاری").fill("قصهٔ آزمایشی فارسی");
  await page
    .getByRole("combobox", { name: "موسیقی" })
    .selectOption("calm-local");
  await page.getByRole("button", { name: "ادامه", exact: true }).click();
  await page.getByRole("button", { name: "ذخیره و ساخت پیش‌نمایش" }).click();

  await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/, { timeout: 30_000 });
  await expect(
    page.getByRole("heading", { name: "قصهٔ آزمایشی فارسی" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "انتخاب به‌عنوان جلد" }),
  ).toBeVisible();
  const privateImage = page.getByRole("img", { name: "photo.png" });
  await expect(privateImage).toBeVisible();
  await expect
    .poll(() =>
      privateImage.evaluate((image: HTMLImageElement) => image.naturalWidth),
    )
    .toBeGreaterThan(0);
  await expect(page.getByRole("slider", { name: "شروع برش" })).toBeVisible();
  await expect(page.getByText("خروجی و اشتراک")).toBeVisible();

  const deletion = await request.delete("/api/auth/account", {
    headers: { authorization: `Bearer ${token}` },
  });
  expect(deletion.ok()).toBeTruthy();
});

test("landing page is RTL, focused, and has no professional timeline controls", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(
    page.getByRole("heading", { name: /صدات را بگو/ }),
  ).toBeVisible();
  await expect(page.getByText(/زیرنویس فارسی هماهنگ/)).toBeVisible();
  await expect(page.getByText(/تایم‌لاین|کی‌فریم|لایه‌بندی/)).toHaveCount(0);
});
