const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";

export type Project = {
  id: string;
  status: string;
  title: string | null;
  secondary_line: string | null;
  duration_limit_seconds: number;
  template_id: string;
  music_track_id: string | null;
  cover_media_id: string | null;
  current_step: string;
  expires_at: string;
  updated_at: string;
};

type ErrorEnvelope = { error?: { message?: string } };

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init.body ? { "content-type": "application/json" } : {}),
      ...(token ? { authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ErrorEnvelope;
    throw new Error(body.error?.message ?? "ارتباط با آواتو برقرار نشد.");
  }
  return (await response.json()) as T;
}

export async function authenticate(
  mode: "register" | "login",
  email: string,
  password: string,
): Promise<string> {
  const body = await apiRequest<{ token: string }>(`/auth/${mode}`, {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return body.token;
}

export function createProject(token: string, title: string, duration: number) {
  return apiRequest<Project>(
    "/projects",
    {
      method: "POST",
      body: JSON.stringify({
        title: title || null,
        duration_limit_seconds: duration,
      }),
    },
    token,
  );
}

export function updateProject(
  token: string,
  projectId: string,
  changes: Record<string, string | null>,
) {
  return apiRequest<Project>(
    `/projects/${projectId}`,
    { method: "PATCH", body: JSON.stringify(changes) },
    token,
  );
}

export async function uploadAsset(
  token: string,
  projectId: string,
  kind: "audio" | "media",
  blob: Blob,
  filename: string,
) {
  const response = await fetch(`${API_URL}/projects/${projectId}/${kind}`, {
    method: kind === "audio" ? "PUT" : "POST",
    headers: {
      authorization: `Bearer ${token}`,
      "content-type": blob.type || "application/octet-stream",
      "x-filename": encodeURIComponent(filename),
    },
    body: blob,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ErrorEnvelope;
    throw new Error(body.error?.message ?? "بارگذاری فایل انجام نشد.");
  }
  return response.json() as Promise<Record<string, unknown>>;
}

export async function replaceMedia(
  token: string,
  projectId: string,
  mediaId: string,
  file: File,
) {
  const response = await fetch(
    `${API_URL}/projects/${projectId}/media/${mediaId}`,
    {
      method: "PUT",
      headers: {
        authorization: `Bearer ${token}`,
        "content-type": file.type || "application/octet-stream",
        "x-filename": encodeURIComponent(file.name),
      },
      body: file,
    },
  );
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ErrorEnvelope;
    throw new Error(body.error?.message ?? "جایگزینی رسانه انجام نشد.");
  }
  return response.json() as Promise<Record<string, unknown>>;
}

export function listProjects(token: string) {
  return apiRequest<{ items: Project[] }>("/projects", {}, token);
}

export function deleteProject(token: string, projectId: string) {
  return apiRequest<{ deleted: boolean }>(
    `/projects/${projectId}`,
    { method: "DELETE" },
    token,
  );
}
