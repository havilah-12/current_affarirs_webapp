import { api } from "./client.js";

/**
 * Saved-article endpoints + download helpers.
 *
 * Downloads are kicked off client-side by creating a temporary object URL
 * from an `arraybuffer` response and clicking a hidden `<a>`. The auth
 * header still rides along via the axios instance, so we don't need to
 * hand-craft a `fetch` for it.
 */

function toPayload(article, { starred = false } = {}) {
  return {
    title: article.title,
    description: article.description ?? null,
    content: article.content ?? null,
    source: article.source ?? null,
    url: article.url ?? null,
    image_url: article.image_url ?? null,
    published_at: article.published_at ?? null,
    category: article.category ?? null,
    starred,
  };
}

export async function saveArticle(article, options) {
  const { data } = await api.post("/saved", toPayload(article, options));
  return data;
}

export async function listSaved({ starredOnly = false } = {}) {
  const { data } = await api.get("/saved", {
    params: { starred_only: starredOnly },
  });
  return data;
}

export async function updateSaved(id, { starred }) {
  const { data } = await api.patch(`/saved/${id}`, { starred });
  return data;
}

export async function deleteSaved(id) {
  const { data } = await api.delete(`/saved/${id}`);
  return data;
}

/**
 * Trigger a browser download of a single saved article.
 *
 * @param {number} id      - saved-article id
 * @param {"txt"|"pdf"} format
 */
export async function downloadSaved(id, { format = "pdf" } = {}) {
  const response = await api.get(`/saved/${id}/download`, {
    params: { format },
    responseType: "blob",
  });
  triggerBlobDownload(response, defaultFilename(`article_${id}`, format));
}

/**
 * Trigger a bulk download of every saved article (or just starred ones).
 */
export async function exportAllSaved({
  format = "pdf",
  starredOnly = false,
} = {}) {
  const response = await api.get("/saved/export", {
    params: { format, starred_only: starredOnly },
    responseType: "blob",
  });
  triggerBlobDownload(
    response,
    defaultFilename(`saved_articles${starredOnly ? "_starred" : ""}`, format)
  );
}

// ---------------------------------------------------------------------------
// Internals
// ---------------------------------------------------------------------------

function defaultFilename(base, ext) {
  const safe = base.replace(/[^A-Za-z0-9._-]+/g, "_").slice(0, 80) || "article";
  return `${safe}.${ext}`;
}

function filenameFromContentDisposition(header) {
  if (!header || typeof header !== "string") return null;
  const match =
    header.match(/filename\*=UTF-8''([^;]+)/i) ||
    header.match(/filename="?([^";]+)"?/i);
  if (!match) return null;
  try {
    return decodeURIComponent(match[1].trim());
  } catch {
    return match[1].trim();
  }
}

function triggerBlobDownload(response, fallbackName) {
  const suggested =
    filenameFromContentDisposition(response.headers["content-disposition"]) ||
    fallbackName;

  const blob = new Blob([response.data], {
    type: response.headers["content-type"] || "application/octet-stream",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = suggested;
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Revoke on next tick so the browser has time to start the download.
  setTimeout(() => URL.revokeObjectURL(url), 250);
}
