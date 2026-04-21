# Current Affairs — Frontend

React + Tailwind UI for the Current Affairs / GK study webapp. Talks to the
FastAPI backend in `../backend` over HTTP and lets users log in, browse the
headline feed (`GET /news`), filter by category / country / Indian state /
keyword, bookmark articles, star them, track a daily reading streak, and
download saved items as `.txt` or `.pdf`.

---

## Stack

- **React 18** (JavaScript, JSX) — no TypeScript to keep setup minimal
- **Vite 5** — dev server + bundler
- **Tailwind CSS 3** — styling, with a small set of reusable component classes in `src/index.css`
- **React Router v6** — client routing
- **axios** — HTTP client with a JWT request interceptor + 401 redirect logic
- **React Context** — auth state; JWT persisted in `localStorage`

No state library (Zustand/Redux/Tanstack Query) — the app is small enough
that `useState` + a single `AuthContext` keep things simple.

---

## Project layout

```text
frontend/
  index.html
  package.json
  vite.config.js
  tailwind.config.js
  postcss.config.js
  .env.example
  .gitignore
  src/
    index.css                # Tailwind + reusable `.btn`, `.input`, `.card`, `.chip` classes
    main.jsx                 # Vite entry -> <BrowserRouter> + <AuthProvider>
    App.jsx                  # <Routes>
    api/
      client.js              # axios instance, JWT interceptor, getToken/setToken, apiErrorMessage
      auth.js                # signup, login (OAuth2 form), fetchMe
      news.js                # fetchNews, CATEGORIES, COUNTRIES, REGIONS_BY_COUNTRY, regionsForCountry
      saved.js               # CRUD + downloadSaved / exportAllSaved (blob -> <a download>)
      activity.js            # pingActivity, getActivityStats (daily streak)
    context/
      AuthContext.jsx        # useAuth(), AuthProvider
    components/
      Navbar.jsx
      ProtectedRoute.jsx
      FiltersBar.jsx
      NewsArticleCard.jsx      # feed card: image, title, excerpt, save button
      SavedArticleCard.jsx   # saved item with star/delete/download controls
      StreakPanel.jsx        # daily-streak widget shown on the dashboard
      Spinner.jsx            # Spinner + FullPageSpinner
    utils/
      time.js                # formatPublished() shared by every article card
    pages/
      LoginPage.jsx
      SignupPage.jsx
      NewsPage.jsx           # home: headline carousel + filters
      SavedPage.jsx          # dashboard: saved articles + streak
```

---

## Quick start

### 1. Install dependencies

```powershell
cd frontend
npm install
```

### 2. Configure the API base URL

```powershell
Copy-Item .env.example .env
```

Default is `VITE_API_BASE_URL=/api`. In dev, Vite's proxy rewrites `/api/*`
to `http://localhost:8000/*`, so the backend can stay on port 8000 without
any CORS dance. For production builds, set `VITE_API_BASE_URL` to the
full backend origin (e.g. `https://api.example.com`).

### 3. Start the backend first

In a separate terminal:

```powershell
cd ..\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### 4. Start the dev server

```powershell
npm run dev
```

Open <http://localhost:5173>. The backend's CORS config already whitelists
this origin.

---

## Routes

| Path       | Auth     | Description                                                            |
|------------|----------|------------------------------------------------------------------------|
| `/login`   | public   | Email + password login form.                                           |
| `/signup`  | public   | Create account; redirects to `/` on success.                           |
| `/`        | required | News carousel (`GET /news`). Category / country / state / search filters. |
| `/saved`   | required | Dashboard. Daily streak + saved articles with downloads.               |

`ProtectedRoute` wraps the private routes. While the auth context is
bootstrapping (validating a stored JWT against `/auth/me`) it renders a
full-page spinner rather than flashing the login screen.

---

## Data flow

```text
AuthProvider (context/AuthContext.jsx)
  ├── on mount: if JWT in localStorage, call /auth/me to hydrate user
  ├── login()/signup(): POST credentials -> save JWT -> fetch /auth/me
  └── logout(): wipe JWT + user

api/client.js (axios)
  ├── request interceptor  -> Authorization: Bearer <jwt>
  └── response interceptor -> on 401, clear JWT and window.location = /login
```

Pages call the thin modules in `src/api/*.js`; components stay presentational.

---

## The feed

The News page calls `GET /news` (detailed articles) and renders each row with
`<NewsArticleCard>` — image, title, description/content excerpt, and Save.
Cards are laid out as a horizontal scroll-snap carousel (3 per page on wide
screens, 2 on tablet, 1 on mobile).

The backend still exposes `GET /news/formatted` (YAKE bullet view) for API
clients; the SPA does not use it. **Formatted vs detailed** on downloads is
only on the Saved page (`style` query param), not on the live feed.

Selecting an Indian state sends `qInTitle=<state>` to the backend so
results are headlines *about* that state, not just any article that
mentions it in passing.

The Save button posts the full article snapshot to `POST /saved`, so
downloaded PDF/TXT later keeps working even if the original URL 404s.

---

## Downloads

`src/api/saved.js` handles both single-article and bulk downloads the
same way:

1. Request the endpoint with `responseType: "blob"` (the auth header
   still goes along via the axios instance).
2. Read the `Content-Disposition` header for a server-suggested filename.
3. Create an object URL and click a hidden `<a download>`.
4. Revoke the object URL on the next tick.

The `SavedArticleCard` and the bulk-export bar on `SavedPage` both let
the user pick `format = txt | pdf` and `style = detailed | formatted`
before firing the download.

---

## Common tasks

- **Change colours**: edit the `brand` palette in `tailwind.config.js`.
- **Add a new filter**: extend `DEFAULT_FILTERS` in `NewsPage.jsx`, surface
  a control in `FiltersBar.jsx`, and pass it through to `fetchNews` in
  `src/api/news.js`.
- **Change token storage**: adjust `TOKEN_STORAGE_KEY`, `getToken`, and
  `setToken` in `src/api/client.js`.
- **Production build**: `npm run build` -> `dist/` is static, host it on
  any CDN/static host and point `VITE_API_BASE_URL` at the deployed backend.

---

## Notes

- All private routes are guarded by `ProtectedRoute`. The backend
  additionally enforces auth on every `/news/*`, `/saved/*`, and `/activity/*` endpoint,
  so even a bypass of the client-side guard is safe.
- JWTs live in `localStorage`. This is vulnerable to XSS; if you later
  introduce user-generated HTML, move the token to an `httpOnly` cookie
  on the backend side.
- Image loading is wrapped in an `onerror` handler that hides broken
  images rather than showing the browser's default broken-image icon.
