export default function Spinner({ size = 20, className = "" }) {
  const dim = typeof size === "number" ? `${size}px` : size;
  return (
    <span
      role="status"
      aria-label="Loading"
      className={`inline-block animate-spin rounded-full border-2 border-slate-300 border-t-brand-600 ${className}`}
      style={{ width: dim, height: dim }}
    />
  );
}

export function FullPageSpinner({ label = "Loading..." }) {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <div className="flex flex-col items-center gap-3 text-slate-500">
        <Spinner size={36} />
        <span className="text-sm">{label}</span>
      </div>
    </div>
  );
}
