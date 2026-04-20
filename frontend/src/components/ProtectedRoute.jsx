import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import { FullPageSpinner } from "./Spinner.jsx";

/**
 * Guards a route against unauthenticated access.
 *
 * While the auth context is still bootstrapping (checking a stored JWT
 * against /auth/me) we show a spinner rather than bouncing the user to
 * /login - otherwise a valid logged-in user would see a login flash on
 * every hard refresh.
 */
export default function ProtectedRoute({ children }) {
  const { isAuthed, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <FullPageSpinner label="Loading session..." />;

  if (!isAuthed) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
