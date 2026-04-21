import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { pingActivity } from "../api/activity.js";
import { apiErrorMessage } from "../api/client.js";
import { fetchNews } from "../api/news.js";
import { saveArticle } from "../api/saved.js";
import FiltersBar from "../components/FiltersBar.jsx";
import NewsArticleCard from "../components/NewsArticleCard.jsx";
import { FullPageSpinner } from "../components/Spinner.jsx";
import Toast from "../components/Toast.jsx";
import { useToast } from "../hooks/useToast.js";



const DEFAULT_FILTERS = {
  category: null,
  country: "in",
  region: null,
  q: "",
};

const PAGE_SIZE = 10;

/**
 * Decode `URLSearchParams` into a `DEFAULT_FILTERS`-shaped object.
 * Anything missing from the URL falls back to the default.
 *
 * Accepts the legacy `state` param too so old bookmarks keep working.
 */
function paramsToFilters(searchParams) {
  return {
    category: searchParams.get("category") || DEFAULT_FILTERS.category,
    country: searchParams.get("country") || DEFAULT_FILTERS.country,
    region:
      searchParams.get("region") ||
      searchParams.get("state") ||
      DEFAULT_FILTERS.region,
    q: searchParams.get("q") || DEFAULT_FILTERS.q,
  };
}

/**
 * Encode a filters object back to a plain `{key: value}` map for
 * `setSearchParams`. Empty / default values are omitted so the URL stays
 * tidy (we don't want `?country=in&q=&region=` everywhere).
 */
function filtersToParams(filters) {
  const out = {};
  if (filters.category) out.category = filters.category;
  if (filters.country) out.country = filters.country;
  if (filters.region) out.region = filters.region;
  if (filters.q && filters.q.trim()) out.q = filters.q.trim();
  return out;
}

export default function NewsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  // Memoize on the URL string (stable across re-renders) rather than the
  // URLSearchParams instance (which react-router may recreate per render).
  const searchKey = searchParams.toString();
  const filters = useMemo(
    () => paramsToFilters(searchParams),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [searchKey]
  );

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [savingUrl, setSavingUrl] = useState(null);
  const [savedUrls, setSavedUrls] = useState(() => new Set());

  const { toast, showToast } = useToast();
  const scrollerRef = useRef(null);

  // Daily-streak: record this visit (idempotent within a UTC day on the
  // backend). Fire and forget - failures are non-fatal to the news view.
  useEffect(() => {
    pingActivity().catch(() => {});
  }, []);

  // Update the URL when FiltersBar fires a change. `replace: true` keeps
  // each filter tweak from polluting the browser history stack.
  const updateFilters = useCallback(
    (next) => setSearchParams(filtersToParams(next), { replace: true }),
    [setSearchParams]
  );

  const load = useCallback(async (current) => {
    setLoading(true);
    setError(null);
    try {
      // The selected region (state / province / emirate / etc.) goes through
      // `qInTitle` so NewsData.io returns articles whose HEADLINE mentions
      // the region - a much tighter filter than the broad `q`, which scans
      // body text and pulls in tangential mentions.
      const res = await fetchNews({
        category: current.category || undefined,
        country: current.country || undefined,
        q: current.q?.trim() || undefined,
        qInTitle: current.region || undefined,
        page: 1,
        pageSize: PAGE_SIZE,
      });
      setData(res);
    } catch (err) {
      setError(apiErrorMessage(err, "Failed to load news."));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(filters);
  }, [load, filters]);

  // When new data arrives, reset the carousel to the start so the user
  // always sees page 1 first.
  useEffect(() => {
    if (scrollerRef.current) {
      scrollerRef.current.scrollTo({ left: 0, behavior: "auto" });
    }
  }, [data]);

  async function handleSave(article) {
    const key = article.url || article.title;
    setSavingUrl(key);
    try {
      await saveArticle(article);
      setSavedUrls((prev) => {
        const next = new Set(prev);
        next.add(key);
        return next;
      });
      showToast("Article saved.");
    } catch (err) {
      showToast(apiErrorMessage(err, "Failed to save."), "error");
    } finally {
      setSavingUrl(null);
    }
  }

  const articles = data?.articles ?? [];

  const resultMeta = useMemo(() => {
    if (!data) return null;
    const count = articles.length;
    const total = data.total_results ?? count;
    return `${count} shown${total && total !== count ? ` of ${total}` : ""}`;
  }, [data, articles.length]);

  /**
   * Scroll the carousel by one "page" (one viewport-width step) in the
   * requested direction. Browser scroll-snap snaps the nearest card into
   * view, so the 3-card layout stays aligned.
   */
  function scrollByPage(direction) {
    const el = scrollerRef.current;
    if (!el) return;
    const step = el.clientWidth; // exactly one page == 3 cards
    el.scrollBy({ left: direction * step, behavior: "smooth" });
  }

  return (
    <div className="space-y-6">
      <FiltersBar
        filters={filters}
        onChange={updateFilters}
        onSubmitSearch={() => load(filters)}
      />

      <div className="flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-brand-800">Latest headlines</h2>
        <div className="flex items-center gap-3">
          {resultMeta && <span className="text-xs text-slate-500">{resultMeta}</span>}
          <button
            type="button"
            onClick={() => load(filters)}
            disabled={loading}
            className="btn-secondary whitespace-nowrap disabled:cursor-not-allowed disabled:opacity-60"
            title="Refetch the latest headlines with the current filters"
          >
            {loading ? "Refreshing..." : "Latest news"}
          </button>
        </div>
      </div>

      {loading ? (
        <FullPageSpinner label="Fetching headlines..." />
      ) : error ? (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        >
          {error}
        </div>
      ) : articles.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
          No articles match these filters. Try a different category, country,
          or clear the search.
        </div>
      ) : (
        <Carousel
          scrollerRef={scrollerRef}
          onPrev={() => scrollByPage(-1)}
          onNext={() => scrollByPage(1)}
        >
          {articles.map((article, idx) => {
            const key = article.url || `${article.title}-${idx}`;
            const isSaved = savedUrls.has(article.url || article.title);
            const isSaving = savingUrl === (article.url || article.title);

            return (
              <div
                key={key}
                className="flex w-full shrink-0 snap-start sm:w-1/2 lg:w-1/3"
              >
                {/* inner padding creates the visual gap between cards
                    without breaking scroll-snap alignment; the inner
                    div stretches so every card in a row matches height */}
                <div className="flex w-full px-2">
                  <div className="flex w-full">
                    <NewsArticleCard
                      article={article}
                      onSave={() => handleSave(article)}
                      isSaving={isSaving}
                      isSaved={isSaved}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </Carousel>
      )}

      <Toast toast={toast} />
    </div>
  );
}

/**
 * Horizontal swipe carousel.
 *
 * - Uses native CSS scroll-snap + `overflow-x-auto` so touch swipe, trackpad
 *   swipe, and shift-scroll all work out of the box without an extra lib.
 * - Prev/next buttons translate to one viewport-width scroll step (which
 *   matches exactly 3 cards on large screens, 2 on sm, 1 on mobile).
 */
function Carousel({ children, scrollerRef, onPrev, onNext }) {
  return (
    <div className="relative">
      {/* Prev button */}
      <button
        type="button"
        aria-label="Previous"
        onClick={onPrev}
        className="absolute left-0 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2 hidden h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 shadow-md transition hover:bg-slate-50 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 sm:flex"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="h-5 w-5"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {/* Next button */}
      <button
        type="button"
        aria-label="Next"
        onClick={onNext}
        className="absolute right-0 top-1/2 z-10 translate-x-1/2 -translate-y-1/2 hidden h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 shadow-md transition hover:bg-slate-50 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 sm:flex"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="h-5 w-5"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {/* Scroller - negative margin cancels the card inner padding so the
          carousel spans the full content width */}
      <div
        ref={scrollerRef}
        className="scrollbar-soft -mx-2 flex snap-x snap-mandatory items-stretch gap-0 overflow-x-auto scroll-smooth pb-3"
        style={{ scrollbarWidth: "thin" }}
      >
        {children}
      </div>
    </div>
  );
}
