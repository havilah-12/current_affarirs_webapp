import { useCallback, useEffect, useState } from "react";

import { apiErrorMessage } from "../api/client.js";
import {
  deleteSaved,
  downloadSaved,
  exportAllSaved,
  listSaved,
  updateSaved,
} from "../api/saved.js";
import SavedArticleCard from "../components/SavedArticleCard.jsx";
import Spinner, { FullPageSpinner } from "../components/Spinner.jsx";
import StreakPanel from "../components/StreakPanel.jsx";
import Toast from "../components/Toast.jsx";
import { useToast } from "../hooks/useToast.js";

/**
 * "Saved" page.
 *
 * Lists the current user's bookmarked articles, lets them:
 *   - filter by starred only
 *   - star / unstar
 *   - delete
 *   - download individually (txt/pdf x detailed/formatted)
 *   - bulk export everything (or just starred)
 */
export default function SavedPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [starredOnly, setStarredOnly] = useState(false);

  // per-row busy flags keyed by article id
  const [busy, setBusy] = useState({});

  // bulk export controls
  const [bulkFormat, setBulkFormat] = useState("pdf");
  const [bulkStyle, setBulkStyle] = useState("formatted");
  const [bulkBusy, setBulkBusy] = useState(false);

  const { toast, showToast } = useToast();

  const load = useCallback(async (starred) => {
    setLoading(true);
    setError(null);
    try {
      const data = await listSaved({ starredOnly: starred });
      setItems(data);
    } catch (err) {
      setError(apiErrorMessage(err, "Failed to load saved articles."));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(starredOnly);
  }, [load, starredOnly]);

  function setRowBusy(id, key, value) {
    setBusy((prev) => ({
      ...prev,
      [id]: { ...(prev[id] || {}), [key]: value },
    }));
  }

  async function handleToggleStar(article) {
    setRowBusy(article.id, "star", true);
    try {
      const updated = await updateSaved(article.id, { starred: !article.starred });
      setItems((prev) =>
        prev.map((item) => (item.id === article.id ? updated : item))
      );
    } catch (err) {
      showToast(apiErrorMessage(err, "Failed to update."), "error");
    } finally {
      setRowBusy(article.id, "star", false);
    }
  }

  async function handleDelete(article) {
    if (!window.confirm(`Remove "${article.title}" from saved?`)) return;
    setRowBusy(article.id, "delete", true);
    try {
      await deleteSaved(article.id);
      setItems((prev) => prev.filter((item) => item.id !== article.id));
      showToast("Article removed.");
    } catch (err) {
      showToast(apiErrorMessage(err, "Failed to delete."), "error");
      setRowBusy(article.id, "delete", false);
    }
  }

  async function handleDownload(article, { format, style }) {
    setRowBusy(article.id, "download", true);
    try {
      await downloadSaved(article.id, { format, style });
    } catch (err) {
      showToast(apiErrorMessage(err, "Download failed."), "error");
    } finally {
      setRowBusy(article.id, "download", false);
    }
  }

  async function handleBulkExport() {
    setBulkBusy(true);
    try {
      await exportAllSaved({
        format: bulkFormat,
        style: bulkStyle,
        starredOnly,
      });
    } catch (err) {
      showToast(apiErrorMessage(err, "Export failed."), "error");
    } finally {
      setBulkBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        </div>

        <label className="inline-flex select-none items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
            checked={starredOnly}
            onChange={(e) => setStarredOnly(e.target.checked)}
          />
          Starred only
        </label>
      </header>

      <StreakPanel />

      {/* Bulk export bar */}
      <section className="card flex flex-col gap-3 p-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex flex-wrap gap-3">
          <div>
            <label className="label" htmlFor="bulk-format">
              Format
            </label>
            <select
              id="bulk-format"
              value={bulkFormat}
              onChange={(e) => setBulkFormat(e.target.value)}
              className="input py-1.5 text-sm"
            >
              <option value="pdf">PDF</option>
              <option value="txt">Plain text</option>
            </select>
          </div>
          <div>
            <label className="label" htmlFor="bulk-style">
              Style
            </label>
            <select
              id="bulk-style"
              value={bulkStyle}
              onChange={(e) => setBulkStyle(e.target.value)}
              className="input py-1.5 text-sm"
            >
              <option value="formatted">Formatted (quick read)</option>
              <option value="detailed">Detailed (full articles)</option>
            </select>
          </div>
        </div>
        <button
          type="button"
          onClick={handleBulkExport}
          disabled={bulkBusy || items.length === 0}
          className="btn-primary"
        >
          {bulkBusy ? (
            <>
              <Spinner size={14} /> Preparing...
            </>
          ) : starredOnly ? (
            "Download starred"
          ) : (
            "Download all"
          )}
        </button>
      </section>

      {loading ? (
        <FullPageSpinner label="Loading saved articles..." />
      ) : error ? (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        >
          {error}
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
          {starredOnly
            ? "No starred articles yet. Star something from the Home page."
            : "No saved articles yet. Head to Home and save a few."}
        </div>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2">
          {items.map((article) => (
            <SavedArticleCard
              key={article.id}
              article={article}
              onToggleStar={() => handleToggleStar(article)}
              onDelete={() => handleDelete(article)}
              onDownload={(opts) => handleDownload(article, opts)}
              busy={busy[article.id]}
            />
          ))}
        </div>
      )}

      <Toast toast={toast} />
    </div>
  );
}
