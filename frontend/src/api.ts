import type { BuildResponse, CatalogResponse, PreviewResponse, SiteSpec } from "./types";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function fetchCatalog() {
  return request<CatalogResponse>("/api/catalog");
}

export function previewSite(spec: SiteSpec) {
  return request<PreviewResponse>("/api/preview", {
    method: "POST",
    body: JSON.stringify(spec),
  });
}

export function exportSite(spec: SiteSpec) {
  return request<BuildResponse>("/api/export", {
    method: "POST",
    body: JSON.stringify(spec),
  });
}
