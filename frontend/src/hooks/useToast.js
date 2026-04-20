import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Tiny one-line toast notifier shared across pages.
 *
 * Usage:
 *   const { toast, showToast } = useToast();
 *   showToast("Article saved.");                // success (default)
 *   showToast("Failed to delete.", "error");    // red variant
 *   return (<>... <Toast toast={toast} /></>);
 *
 * Implementation notes:
 * - Only one toast is visible at a time. A second `showToast()` call
 *   replaces the first and resets the auto-dismiss timer.
 * - The dismiss timer is cleared on unmount so we don't `setState` on a
 *   torn-down component.
 */
export function useToast({ duration = 2500 } = {}) {
  const [toast, setToast] = useState(null);
  const timerRef = useRef(null);

  const showToast = useCallback(
    (message, kind = "success") => {
      if (timerRef.current) clearTimeout(timerRef.current);
      setToast({ message, kind });
      timerRef.current = setTimeout(() => setToast(null), duration);
    },
    [duration]
  );

  useEffect(
    () => () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    },
    []
  );

  return { toast, showToast };
}
