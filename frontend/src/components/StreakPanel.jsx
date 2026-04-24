import { useCallback, useEffect, useState } from "react";

import { getActivityStats } from "../api/activity.js";

/** Emoji per NewsData.io category (matches FiltersBar / backend). */
const CATEGORY_ICONS = {
  business: "💼",
  crime: "⚖️",
  domestic: "🏠",
  education: "🎓",
  entertainment: "🎬",
  environment: "🌱",
  food: "🍽",
  health: "🏥",
  lifestyle: "✨",
  other: "📋",
  politics: "🏛",
  science: "🔬",
  sports: "⚽",
  technology: "💻",
  top: "⭐",
  tourism: "✈",
  world: "🌍",
};

/**
 * Daily-reading-streak widget shown at the top of the Dashboard.
 *
 * Four headline metrics, 30-day consistency, and a month calendar (UTC) with
 * category icons on days the user read from Home. Visiting Home once a UTC
 * day (with a category filter) records that day and tag.
 */
export default function StreakPanel() {
  const [view, setView] = useState(utcCurrentMonth);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    return getActivityStats(view.y, view.m)
      .then((data) => {
        setStats(data);
        setError(null);
      })
      .catch(() => {
        setError("Couldn't load streak stats.");
      });
  }, [view.y, view.m]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    load().finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [load]);

  if (loading) {
    return (
      <section className="card animate-pulse p-5">
        <div className="h-4 w-40 rounded bg-slate-200" />
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-16 rounded-xl bg-slate-100" />
          ))}
        </div>
      </section>
    );
  }

  if (error || !stats) {
    return (
      <section className="card p-5 text-sm text-slate-500">
        {error ?? "No activity yet."}
      </section>
    );
  }

  const days30 = buildHeatmapCells(stats);
  const readDays30 = days30.filter((d) => d.read).length;
  const consistencyPct = Math.round((readDays30 / days30.length) * 100);
  const streakHint = stats.read_today
    ? "Great momentum - keep the streak alive tomorrow."
    : "Open Home once today to avoid breaking your streak.";

  const readMap = new Map(
    (stats.read_days_in_month || []).map((r) => [String(r.day).slice(0, 10), r.category]),
  );
  const nextMonthDisabled = isNextMonthBeyondCurrent(shiftMonth(view, 1), stats.today);

  return (
    <section className="card overflow-hidden p-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Daily reading goal</h2>
          <p className="mt-0.5 text-sm text-slate-500">{streakHint}</p>
        </div>
        <span
          className={
            "rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide " +
            (stats.read_today
              ? "bg-emerald-100 text-emerald-700"
              : "bg-accent-100 text-accent-700")
          }
        >
          {stats.read_today ? "Read today ✓" : "Not read today"}
        </span>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat
          label="Current streak"
          value={stats.current_streak}
          suffix={stats.current_streak === 1 ? "day" : "days"}
          accent
        />
        <Stat
          label="Longest streak"
          value={stats.longest_streak}
          suffix={stats.longest_streak === 1 ? "day" : "days"}
        />
        <Stat label="This month" value={stats.days_this_month} suffix="days" />
        <Stat label="Lifetime" value={stats.total_days} suffix="days" />
      </div>

      <div className="mt-4 rounded-xl border border-slate-200 bg-white/70 px-4 py-3">
        <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-slate-500">
          <span>30-day consistency</span>
          <span>{consistencyPct}%</span>
        </div>
        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full rounded-full bg-brand-500 transition-all"
            style={{ width: `${consistencyPct}%` }}
          />
        </div>
      </div>

      <div className="mt-6">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-slate-800">Your calendar</h3>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setView((v) => shiftMonth(v, -1))}
              className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-sm text-slate-700 shadow-sm transition hover:bg-slate-50"
              aria-label="Previous month"
            >
              ←
            </button>
            <span className="min-w-[10rem] text-center text-sm font-medium text-slate-800">
              {formatMonthLabel(stats.calendar_year, stats.calendar_month)}
            </span>
            <button
              type="button"
              onClick={() => setView((v) => shiftMonth(v, 1))}
              disabled={nextMonthDisabled}
              className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-sm text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              aria-label="Next month"
            >
              →
            </button>
          </div>
        </div>

        <div className="mb-2 grid grid-cols-7 gap-1 text-center text-[10px] font-semibold uppercase tracking-wide text-slate-500">
          {WEEKDAYS.map((d) => (
            <div key={d} className="px-0.5">
              {d}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1.5">
          {buildMonthGridCells(
            stats.calendar_year,
            stats.calendar_month,
            String(stats.today).slice(0, 10),
          ).map((cell) => {
            if (cell.kind === "pad") {
              return <div key={cell.k} className="min-h-[2.5rem]" />;
            }
            const cat = readMap.get(cell.iso);
            const read = readMap.has(cell.iso);
            const showIcon = read && cat;
            return (
              <div
                key={cell.iso}
                title={tooltipForCell(
                  cell.iso,
                  read,
                  cat,
                  String(stats.today).slice(0, 10),
                )}
                className={
                  "flex min-h-[2.5rem] flex-col items-center justify-center rounded-lg border text-xs transition " +
                  (read
                    ? "border-emerald-200/80 bg-emerald-100"
                    : cell.isToday
                    ? "border-dashed border-brand-300 bg-slate-50"
                    : "border-slate-200 bg-slate-50/80")
                }
              >
                <span
                  className={
                    "text-[10px] font-medium " + (read ? "text-emerald-700" : "text-slate-500")
                  }
                >
                  {cell.d}
                </span>
                {read ? (
                  <span
                    className={
                      "text-base leading-none " +
                      (showIcon ? "" : "font-semibold text-emerald-700")
                    }
                    aria-hidden
                  >
                    {showIcon ? iconForCategory(cat) : "✓"}
                  </span>
                ) : (
                  <span className="h-3" />
                )}
              </div>
            );
          })}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-3 w-3 rounded border border-slate-200 bg-slate-50" />
            Missed
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-3 w-3 rounded border border-emerald-200/80 bg-emerald-100" />
            Read
          </span>
        </div>
      </div>
    </section>
  );
}

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function utcCurrentMonth() {
  const t = new Date();
  return { y: t.getUTCFullYear(), m: t.getUTCMonth() + 1 };
}

function formatMonthLabel(y, m) {
  return new Intl.DateTimeFormat("en", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(y, m - 1, 1)));
}

function shiftMonth(v, delta) {
  const t = new Date(Date.UTC(v.y, v.m - 1 + delta, 1));
  return { y: t.getUTCFullYear(), m: t.getUTCMonth() + 1 };
}

/** True if (year, month) is after the current calendar month in UTC. */
function isNextMonthBeyondCurrent(nv, todayVal) {
  const [y, m] = String(todayVal).slice(0, 10).split("-").map(Number);
  if (nv.y > y) return true;
  if (nv.y < y) return false;
  return nv.m > m;
}

function daysInMonthUtc(y, m) {
  return new Date(Date.UTC(y, m, 0)).getUTCDate();
}

function toIsoYMD(y, m, d) {
  return [y, String(m).padStart(2, "0"), String(d).padStart(2, "0")].join("-");
}

function buildMonthGridCells(y, m, todayIso) {
  const dim = daysInMonthUtc(y, m);
  const firstDow = new Date(Date.UTC(y, m - 1, 1)).getUTCDay();
  const cells = [];
  let k = 0;
  for (let i = 0; i < firstDow; i++) {
    cells.push({ kind: "pad", k: k++ });
  }
  for (let d = 1; d <= dim; d++) {
    const iso = toIsoYMD(y, m, d);
    cells.push({ kind: "day", d, iso, isToday: iso === todayIso });
  }
  const tail = (7 - (cells.length % 7)) % 7;
  for (let i = 0; i < tail; i++) {
    cells.push({ kind: "pad", k: k++ });
  }
  return cells;
}

function iconForCategory(cat) {
  if (!cat) return "📰";
  const k = String(cat).toLowerCase();
  return CATEGORY_ICONS[k] || "📰";
}

function tooltipForCell(iso, read, cat, todayIso) {
  if (read) {
    const c = cat ? ` · ${cat}` : "";
    return `${iso} — read${c}`;
  }
  if (iso < todayIso) {
    return `${iso} — Missed`;
  }
  if (iso === todayIso) {
    return `${iso} — Open Home to count today`;
  }
  return `${iso} — not yet`;
}

function Stat({ label, value, suffix, accent = false }) {
  return (
    <div
      className={
        "rounded-xl border px-4 py-3 " +
        (accent
          ? "border-brand-200 bg-brand-50"
          : "border-slate-200 bg-slate-50")
      }
    >
      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 flex items-baseline gap-1">
        <span
          className={
            "text-2xl font-bold " + (accent ? "text-brand-700" : "text-slate-900")
          }
        >
          {value}
        </span>
        <span className="text-xs text-slate-500">{suffix}</span>
      </div>
    </div>
  );
}

/**
 * Build the 30 (today-anchored) cells for the heatmap. Marked-read cells
 * come from `stats.last_30_days`. Today is highlighted with a subtle ring.
 */
function buildHeatmapCells(stats) {
  const readSet = new Set(stats.last_30_days);
  const todayIso = stats.today;
  const today = parseIso(todayIso);
  const out = [];
  for (let i = 29; i >= 0; i--) {
    const d = new Date(today);
    d.setUTCDate(today.getUTCDate() - i);
    const iso = toIso(d);
    out.push({ iso, read: readSet.has(iso), isToday: iso === todayIso });
  }
  return out;
}

function parseIso(iso) {
  const [y, m, d] = String(iso).split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

function toIso(d) {
  return [
    d.getUTCFullYear(),
    String(d.getUTCMonth() + 1).padStart(2, "0"),
    String(d.getUTCDate()).padStart(2, "0"),
  ].join("-");
}
