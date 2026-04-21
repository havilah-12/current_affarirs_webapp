import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const navLinkClass = ({ isActive }) =>
  [
    "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
    isActive
      ? "bg-brand-100 text-brand-700"
      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
  ].join(" ");

export default function Navbar() {
  const { isAuthed, user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/70 shadow-sm backdrop-blur-md">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link to="/" className="group flex items-center gap-3">
          <BrandMark />
          <span className="flex flex-col leading-tight">
            <span className="text-2xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              Current Affairs
            </span>
            <span className="mt-0.5 hidden text-[11px] font-medium text-slate-500 sm:block">
              All happenings around the world &mdash; in one place.
            </span>
          </span>
        </Link>

        <nav className="flex items-center gap-1">
          {isAuthed ? (
            <>
              <NavLink to="/" end className={navLinkClass}>
                Home
              </NavLink>
              <NavLink to="/saved" className={navLinkClass}>
                Dashboard
              </NavLink>
              <span className="hidden sm:inline px-2 text-xs text-slate-400">
                {user?.email}
              </span>
              <button type="button" onClick={handleLogout} className="btn-ghost">
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className={navLinkClass}>
                Log in
              </NavLink>
              <NavLink to="/signup" className="btn-primary">
                Sign up
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

// Navbar brand logo - uses /public/logo.png.
//
// The PNG has a near-white background baked in (not pure #FFF), so plain
// mix-blend-multiply leaves a faint square halo. Wrapping the image in a
// `rounded-full` container with `overflow-hidden` physically crops the square
// corners into a clean circular badge - any leftover off-white pixels live
// inside the circle and blend with the white-ish navbar.
function BrandMark() {
  return (
    <span className="relative flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-full bg-white ring-1 ring-slate-200/70 transition-transform duration-500 ease-out group-hover:rotate-[18deg]">
      <img
        src="/logo.png"
        alt="Current Affairs logo"
        width="56"
        height="56"
        className="h-full w-full object-cover"
        style={{ mixBlendMode: "multiply" }}
      />
    </span>
  );
}
