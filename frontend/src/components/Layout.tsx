import { useEffect, useState } from "react";
import { Link, NavLink, Navigate, Outlet, useLocation } from "react-router-dom";
import { Menu, X, ArrowRight, Moon, Sun } from "lucide-react";
import { useAuth } from "../auth-context";
import { ErrorNotice, Loading } from "./ui";

type Theme = "light" | "dark";

function getInitialTheme(): Theme {
  try {
    const saved = window.localStorage.getItem("skillswap-theme");
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    // Storage may be unavailable in private browsing; use the system preference.
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function Layout() {
  const auth = useAuth(),
    [open, setOpen] = useState(false),
    [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      window.localStorage.setItem("skillswap-theme", theme);
    } catch {
      // Keep the in-memory choice even when the browser blocks storage.
    }
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute("content", theme === "dark" ? "#141216" : "#c83b46");
  }, [theme]);

  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <Link to="/" className="brand" aria-label="SkillSwap home">
          SkillSwap
        </Link>
        <button
          className="theme-toggle"
          type="button"
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          aria-pressed={theme === "dark"}
          onClick={() => setTheme((current) => current === "dark" ? "light" : "dark")}
        >
          {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
          <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
        </button>
        <button
          className="menu-button"
          aria-label={open ? "Close navigation" : "Open navigation"}
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          {open ? <X /> : <Menu />}
        </button>
        <nav
          className={open ? "main-nav open" : "main-nav"}
          aria-label="Main navigation"
          onClick={() => setOpen(false)}
        >
          <NavLink to="/explore">Explore skills</NavLink>
          <Link to="/#how-it-works">How it works</Link>
          <Link to="/profile">Teach a skill</Link>
          {auth.loggedIn && (
            <>
              <NavLink to="/dashboard">My activity</NavLink>
              <NavLink to="/credits">Credits</NavLink>
              {auth.me?.is_admin && <NavLink to="/admin">Admin</NavLink>}
            </>
          )}
          <div className="mobile-account">
            {auth.loggedIn ? (
              <>
                <Link to="/profile">My profile</Link>
                <button className="text-button" onClick={auth.logout}>
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link to="/login">Log in</Link>
                <Link to="/register">Join SkillSwap</Link>
              </>
            )}
          </div>
        </nav>
        <div className="header-account">
          {auth.loggedIn ? (
            <>
              <Link to="/profile" className="account-link">
                {auth.me?.name || "My account"}
              </Link>
              <button className="text-button" onClick={auth.logout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="login-link">
                Log in
              </Link>
              <Link className="button" to="/register">
                Join SkillSwap
              </Link>
            </>
          )}
        </div>
      </header>
      {auth.expired && (
        <div className="session-notice" role="status">
          Your session expired. Log in again to continue; your saved activity is
          safe.
        </div>
      )}
      <main id="main">
        <Outlet />
      </main>
      <footer className="site-footer">
        <Link className="brand" to="/">
          SkillSwap
        </Link>
        <p>Share time. Build skills.</p>
        <Link to="/explore">
          Find a learning partner <ArrowRight size={16} />
        </Link>
        <span>Every member can teach and learn.</span>
      </footer>
    </>
  );
}
export function Protected({ admin = false }: { admin?: boolean }) {
  const auth = useAuth(),
    location = useLocation();
  if (!auth.loggedIn)
    return (
      <Navigate
        replace
        to={
          "/login?returnTo=" +
          encodeURIComponent(location.pathname + location.search)
        }
      />
    );
  if (auth.loading)
    return (
      <div className="container">
        <Loading text="Opening your account…" />
      </div>
    );
  if (auth.error)
    return (
      <div className="container">
        <ErrorNotice error={auth.error} />
      </div>
    );
  if (admin && !auth.me?.is_admin)
    return (
      <div className="container">
        <h1>Administrator access required</h1>
        <p>This page is available to SkillSwap administrators.</p>
        <Link to="/dashboard">Return to your activity</Link>
      </div>
    );
  return <Outlet />;
}
