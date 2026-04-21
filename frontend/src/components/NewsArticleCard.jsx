import Spinner from "./Spinner.jsx";
import { formatPublished } from "../utils/time.js";

/**
 * Headline card for the live feed (`GET /news`): hero image, title, and a
 * short excerpt from description or content.
 *
 * Props:
 *   article    : Article shape from the backend (detailed view)
 *   onSave()   : called when user saves
 *   isSaving   : show spinner on the button
 *   isSaved    : render disabled "Saved" state
 */
function excerpt(article) {
  const text = (article.description || article.content || "").trim();
  if (!text) return null;
  return text;
}

function formatCategoryLabel(category) {
  if (!category || typeof category !== "string") return null;
  return category[0].toUpperCase() + category.slice(1);
}

export default function NewsArticleCard({ article, onSave, isSaving, isSaved }) {
  const published = formatPublished(article.published_at);
  const body = excerpt(article);
  const categoryLabel = formatCategoryLabel(article.category);

  return (
    <article className="card flex h-full w-full flex-col">
      {article.image_url && (
        <img
          src={article.image_url}
          alt=""
          loading="lazy"
          className="aspect-video w-full bg-slate-100 object-cover"
          onError={(e) => {
            e.currentTarget.style.display = "none";
          }}
        />
      )}
      <div className="flex flex-1 flex-col p-4 sm:p-5">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {categoryLabel && <span className="chip-brand">{categoryLabel}</span>}
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

        {article.author && (
          <p className="mt-1 text-xs text-slate-500">By {article.author}</p>
        )}

        {body ? (
          <p className="mt-3 line-clamp-5 text-sm leading-relaxed text-slate-700">{body}</p>
        ) : null}

        {article.keyphrases?.length > 0 && (
          <div className="mt-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-700">
              Key headings
            </p>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {article.keyphrases.map((kp, idx) => (
                <span key={`${kp}-${idx}`} className="chip">
                  {kp}
                </span>
              ))}
            </div>
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
