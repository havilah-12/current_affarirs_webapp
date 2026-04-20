/**
 * Shared "when was this published?" formatter used by every article card.
 *
 * Returns null for missing / unparseable timestamps. Otherwise:
 *   {
 *     label:    "5m ago" | "3h ago" | "Yesterday" | "Apr 18, 2026",
 *     absolute: "Apr 18, 2026, 14:27 IST",   // for tooltip
 *   }
 *
 * The relative phrasing for items < 48 h old makes it obvious which
 * articles are actually fresh - especially helpful when the upstream
 * news API has a few hours of indexing latency on its free tier.
 */
export function formatPublished(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;

  const absolute = d.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  });

  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);

  let label;
  if (diffMs < 0) {
    // Clocks drift / future-dated article: just show the date.
    label = d.toLocaleDateString(undefined, {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } else if (diffMin < 1) {
    label = "Just now";
  } else if (diffMin < 60) {
    label = `${diffMin}m ago`;
  } else if (diffMin < 60 * 24) {
    label = `${Math.floor(diffMin / 60)}h ago`;
  } else if (diffMin < 60 * 48) {
    label = "Yesterday";
  } else {
    label = d.toLocaleDateString(undefined, {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  return { label, absolute };
}
