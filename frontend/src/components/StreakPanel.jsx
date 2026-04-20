import { useEffect, useState } from "react";

import { getActivityStats } from "../api/activity.js";

/**
 * Daily-reading-streak widget shown at the top of the Dashboard.
 *
 * Renders four headline metrics (today, current streak, longest streak,
 * this month) and a 30-day heatmap so the user can see their consistency
 * at a glance. Visiting the Home page once a calendar day (UTC) is enough
 * to keep the streak alive.
 */
export default function StreakPanel() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getActivityStats()
      .then((data) => {
        if (!cancelled) {
          setStats(data);
          setError(null);
        }
      })
      .catch(() => {
        if (!cancelled) setError("Couldn't load streak stats.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

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

  return (
    <section className="card overflow-hidden p-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Daily reading goal</h2>
          <p className="mt-0.5 text-sm text-slate-500">
            Open the news at least once a day to keep your streak alive.
          </p>
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

      <div className="mt-5">
        <div className="mb-2 flex items-center justify-between text-xs text-slate-500">
          <span>Last 30 days</span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-3 w-3 rounded-sm bg-slate-200" />
            <span>Missed</span>
            <span className="ml-2 inline-block h-3 w-3 rounded-sm bg-brand-500" />
            <span>Read</span>
          </span>
        </div>
        <div
          className="grid gap-1"
          style={{ gridTemplateColumns: "repeat(30, minmax(0, 1fr))" }}
        >
          {days30.map((cell) => (
            <div
              key={cell.iso}
              title={`${cell.iso}${cell.read ? " - read" : ""}`}
              className={
                "h-5 w-full rounded-sm transition " +
                (cell.read
                  ? "bg-brand-500 ring-1 ring-brand-600/40"
                  : cell.isToday
                  ? "bg-slate-200 ring-1 ring-brand-300"
                  : "bg-slate-200")
              }
            />
          ))}
        </div>
      </div>
    </section>
  );
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
  // Construct a UTC date so day-arithmetic doesn't drift across DST.
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

function toIso(d) {
  return [
    d.getUTCFullYear(),
    String(d.getUTCMonth() + 1).padStart(2, "0"),
    String(d.getUTCDate()).padStart(2, "0"),
  ].join("-");
}
