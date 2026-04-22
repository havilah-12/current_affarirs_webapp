import { useState } from "react";

import Spinner from "./Spinner.jsx";
import { formatPublished } from "../utils/time.js";

/**
 * Card for a persisted article on the "Saved" page.
 *
 * Responsibilities:
 *   - Show the stored snapshot (title, source, date, description).
 *   - Toggle `starred`.
 *   - Download in txt/pdf.
 *   - Delete.
 *
 * Actions are delegated up to the page via callbacks so all network side
 * effects live in one place (SavedPage).
 */
export default function SavedArticleCard({
  article,
  onToggleStar,
  onDelete,
  onDownload,
  busy, // { star, delete, download } booleans
}) {
  const published = formatPublished(article.published_at);
  const [downloadFormat, setDownloadFormat] = useState("pdf");

  async function handleDownload() {
    await onDownload({ format: downloadFormat });
  }

  return (
    <article className="card flex flex-col p-4 sm:p-5">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        {article.category && (
          <span className="chip-brand">
            {article.category[0].toUpperCase() + article.category.slice(1)}
          </span>
        )}
        {article.source && <span className="chip">{article.source}</span>}
        {published && (
          <span className="text-slate-500" title={published.absolute}>
            {published.label}
          </span>
        )}
        {article.starred && (
          <span className="chip bg-accent-100 text-accent-700">
            ★ Starred
          </span>
        )}
      </div>

      <h3 className="mt-3 text-lg font-semibold leading-snug text-slate-900">
        {article.title}
      </h3>

      {article.description && (
        <p className="mt-2 line-clamp-4 text-sm leading-relaxed text-slate-600">
          {article.description}
        </p>
      )}

      <div className="mt-4 flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3 sm:flex-row sm:items-end">
        <div className="flex flex-1 flex-wrap gap-3">
          <div>
            <label className="label text-xs" htmlFor={`fmt-${article.id}`}>
              Format
            </label>
            <select
              id={`fmt-${article.id}`}
              value={downloadFormat}
              onChange={(e) => setDownloadFormat(e.target.value)}
              className="input py-1.5 text-sm"
            >
              <option value="pdf">PDF</option>
              <option value="txt">Plain text</option>
            </select>
          </div>
        </div>
        <button
          type="button"
          onClick={handleDownload}
          disabled={busy?.download}
          className="btn-primary"
        >
          {busy?.download ? (
            <>
              <Spinner size={14} /> Preparing...
            </>
          ) : (
            "Download"
          )}
        </button>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-2">
        {article.url ? (
          <a
            href={article.url}
            rel="noreferrer"
            className="text-sm font-medium text-brand-600 hover:text-brand-700"
            title="Opens the source page; use the browser Back button to return"
          >
            Open source &rarr;
          </a>
        ) : (
          <span />
        )}

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onToggleStar}
            disabled={busy?.star}
            className="btn-secondary"
            aria-pressed={article.starred}
          >
            {article.starred ? "Unstar" : "Star"}
          </button>
          <button
            type="button"
            onClick={onDelete}
            disabled={busy?.delete}
            className="btn-danger"
          >
            {busy?.delete ? (
              <>
                <Spinner size={14} /> Removing...
              </>
            ) : (
              "Delete"
            )}
          </button>
        </div>
      </div>
    </article>
  );
}
