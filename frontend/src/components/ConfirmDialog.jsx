import { useEffect } from "react";

/**
 * In-app confirm dialog (replaces `window.confirm` for a consistent look).
 */
export default function ConfirmDialog({
  title,
  message,
  confirmLabel = "Delete",
  cancelLabel = "Cancel",
  onConfirm,
  onCancel,
}) {
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onCancel]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-describedby="confirm-dialog-message"
      aria-label={title ? undefined : "Confirmation"}
      aria-labelledby={title ? "confirm-dialog-title" : undefined}
    >
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/45"
        onClick={onCancel}
        aria-label="Close dialog"
      />
      <div
        className="relative z-10 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {title ? (
          <h2 id="confirm-dialog-title" className="text-lg font-semibold text-slate-900">
            {title}
          </h2>
        ) : null}
        <p
          id="confirm-dialog-message"
          className={title ? "mt-2 text-sm leading-relaxed text-slate-600" : "text-sm leading-relaxed text-slate-600"}
        >
          {message}
        </p>
        <div className="mt-6 flex flex-col-reverse justify-end gap-3 sm:flex-row">
          <button type="button" className="btn-secondary w-full sm:w-auto" onClick={onCancel}>
            {cancelLabel}
          </button>
          <button type="button" className="btn-danger w-full sm:w-auto" onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
