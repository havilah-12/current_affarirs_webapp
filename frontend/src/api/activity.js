import { api } from "./client.js";

/**
 * Reading-activity / daily-streak endpoints.
 *
 * `pingActivity` is fire-and-forget from the news page; `getActivityStats`
 * powers the dashboard widgets (streak counter, heatmap, etc.).
 */

export async function pingActivity() {
  const { data } = await api.post("/activity/ping");
  return data;
}

export async function getActivityStats() {
  const { data } = await api.get("/activity/stats");
  return data;
}
