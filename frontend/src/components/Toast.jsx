/**
 * Floating one-line toast.
 *
 * Pairs with `useToast()` from `../hooks/useToast.js`. Render `<Toast />`
 * once at the bottom of a page and pass the `toast` value the hook returns;
 * it disappears automatically when there's nothing to show.
 */
export default function Toast({ toast }) {
  if (!toast) return null;

  const colorClasses =
    toast.kind === "error"
      ? "bg-red-600 text-white"
      : "bg-slate-900 text-white";

  return (
    <div
      role="status"
      className={
        "pointer-events-none fixed bottom-6 left-1/2 z-40 -translate-x-1/2 rounded-full px-4 py-2 text-sm font-medium shadow-lg " +
        colorClasses
      }
    >
      {toast.message}
    </div>
  );
}
