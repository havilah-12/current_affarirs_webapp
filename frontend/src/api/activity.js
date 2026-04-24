import { api } from "./client.js";

/**
 * Reading-activity / daily-streak endpoints.
 *
 * `pingActivity` is fire-and-forget from the news page; `getActivityStats`
 * powers the dashboard widgets (streak counter, heatmap, etc.).
 */

export async function pingActivity({ category } = {}) {
  const { data } = await api.post("/activity/ping", {
    category: category === undefined ? null : category,
  });
  return data;
}

/**
 * @param {number} [viewYear] - UTC calendar year (default: current month on server)
 * @param {number} [viewMonth] - 1–12 (default: with viewYear, or current month on server)
 */
export async function getActivityStats(viewYear, viewMonth) {
  const params = {};
  if (viewYear != null && viewMonth != null) {
    params.cal_year = viewYear;
    params.cal_month = viewMonth;
  }
  const { data } = await api.get("/activity/stats", { params });
  return data;
}
