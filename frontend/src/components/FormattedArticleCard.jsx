import Spinner from "./Spinner.jsx";
import { formatPublished } from "../utils/time.js";

/**
 * Quick-read view: title + a bullet list produced by the backend's
 * formatter (`GET /news/formatted`).
 *
 * Props:
 *   article    : FormattedArticle shape
 *   onSave()   : called when user saves
 *   isSaving   : show spinner on the button
 *   isSaved    : render disabled "Saved" state
 */
export default function FormattedArticleCard({
  article,
  onSave,
  isSaving,
  isSaved,
}) {
  const published = formatPublished(article.published_at);

  return (
    <article className="card flex h-full w-full flex-col">
      {article.image_url && (
        <img
          src={article.image_url}
          alt=""
          loading="lazy"
          className="aspect-video w-full bg-slate-100 object-cover"
          onError={(e) => {
            // Some publishers' image hosts 403 us or stop serving the asset.
            // Hide the broken image so the card still looks clean.
            e.currentTarget.style.display = "none";
          }}
        />
      )}
      <div className="flex flex-1 flex-col p-4 sm:p-5">
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
        </div>

        <h3 className="mt-3 text-lg font-semibold leading-snug text-slate-900">
          {article.title}
        </h3>

        {article.bullets?.length > 0 ? (
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-slate-700">
            {article.bullets.map((bullet, idx) => (
              <li key={idx} className="line-clamp-2">
                {bullet}
              </li>
            ))}
          </ul>
        ) : article.summary ? (
          <p className="mt-3 line-clamp-4 text-sm leading-relaxed text-slate-700">
            {article.summary}
          </p>
        ) : null}

        {article.keyphrases?.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {article.keyphrases.map((kp, idx) => (
              <span key={idx} className="chip">
                {kp}
              </span>
            ))}
          </div>
        )}

        <div className="mt-auto flex flex-wrap items-center justify-between gap-3 pt-4">
          {article.url ? (
            <a
              href={article.url}
              rel="noreferrer"
              className="text-sm font-medium text-brand-600 hover:text-brand-700"
              title="Opens the source page; use the browser Back button to return"
            >
              Source &rarr;
            </a>
          ) : (
            <span />
          )}

          <button
            type="button"
            onClick={onSave}
            disabled={isSaving || isSaved}
            className={isSaved ? "btn-secondary" : "btn-primary"}
          >
            {isSaving ? (
              <>
                <Spinner size={14} /> Saving...
              </>
            ) : isSaved ? (
              "Saved"
            ) : (
              "Save"
            )}
          </button>
        </div>
      </div>
    </article>
  );
}

