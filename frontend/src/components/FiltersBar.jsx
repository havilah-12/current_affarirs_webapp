import { useMemo, useState } from "react";
import { CATEGORIES, COUNTRIES, regionsForCountry } from "../api/news.js";


export default function FiltersBar({ filters, onChange, onSubmitSearch }) {
  const [localQ, setLocalQ] = useState(filters.q ?? "");

  const regions = useMemo(
    () => regionsForCountry(filters.country),
    [filters.country],
  );

  function update(patch) {
    onChange({ ...filters, ...patch });
  }

  function handleSubmit(event) {
    event.preventDefault();
    onChange({ ...filters, q: localQ.trim() });
    onSubmitSearch?.();
  }

  return (
    <section className="card p-4 sm:p-5">
      {/* Single-row filter strip - wraps gracefully on smaller screens */}
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:flex-wrap">
        {/* Category */}
        <div className="w-32 shrink-0">
          <label className="label" htmlFor="filter-category">
            Category
          </label>
          <select
            id="filter-category"
            className="input"
            value={filters.category ?? ""}
            onChange={(e) => update({ category: e.target.value || null })}
          >
            <option value="">Any</option>
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat[0].toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Country */}
        <div className="w-44 shrink-0">
          <label className="label" htmlFor="filter-country">
            Country
          </label>
          <select
            id="filter-country"
            className="input"
            value={filters.country ?? ""}
            onChange={(e) => {
              const next = e.target.value || null;

              
              update({ country: next, region: null });
            }}
          >
            <option value="">Any country</option>
            {COUNTRIES.map((c) => (
              <option key={c.code} value={c.code}>
                {c.label}
              </option>
            ))}
          </select>
        </div>

        {/* Region (only when the selected country has a defined subdivision list) */}
        {regions.length > 0 && (
          <div className="w-44 shrink-0">
            <label className="label" htmlFor="filter-region">
              Region
            </label>
            <select
              id="filter-region"
              className="input"
              value={filters.region ?? ""}
              onChange={(e) => update({ region: e.target.value || null })}
            >
              <option value="">All regions</option>
              {regions.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Search (inline, takes remaining space on wide screens) */}
        <form
          onSubmit={handleSubmit}
          className="flex min-w-[14rem] flex-1 flex-col"
        >
          <label className="label" htmlFor="filter-search">
            Search <span className="font-normal normal-case text-slate-400">(optional)</span>
          </label>
          <div className="flex gap-2">
            <input
              id="filter-search"
              type="search"
              className="input"
              placeholder="search by topic or headline"
              value={localQ}
              onChange={(e) => setLocalQ(e.target.value)}
            />
            <button type="submit" className="btn-primary whitespace-nowrap px-4">
              Go
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
