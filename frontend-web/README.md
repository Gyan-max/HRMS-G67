# Sentinel — React frontend (PR A)

This is the new React frontend for Sentinel. It replaces the Streamlit
landing experience while the legacy Streamlit dashboard (`../frontend/`)
continues to serve live check-ins, trends, and history until PR B ports
the dashboard over.

## Stack

- **Build tool:** [Vite](https://vite.dev/) 8
- **Framework:** React 19 + TypeScript
- **Styling:** [Tailwind CSS](https://tailwindcss.com/) 3 with a custom
  design-token layer
- **UI primitives:** [shadcn/ui](https://ui.shadcn.com/)-style components
  (`Button`, `Card`, `Badge`) — copy-paste, no runtime dependency
- **Routing:** [React Router](https://reactrouter.com/) 6
- **Icons:** [lucide-react](https://lucide.dev/)
- **Utilities:** `clsx`, `tailwind-merge`, `class-variance-authority`

## Local development

```bash
# from frontend-web/
npm install
npm run dev
```

The dev server boots at <http://localhost:5173>.

To point the (future) typed API client at a different backend, copy
`.env.example` to `.env.local` and override `VITE_API_BASE_URL`.

## Production build

```bash
npm run build      # compiles + bundles into dist/
npm run preview    # serve dist/ locally for smoke testing
```

## Deploy to Vercel

`vercel.json` is preconfigured. From the repo root:

```bash
vercel link        # one-time; pick the frontend-web/ folder as the project root
vercel --prod
```

The site is a static SPA, so any host that serves a single-page app
(Vercel, Netlify, Cloudflare Pages, plain S3 + CloudFront) works.

## Project layout

```
frontend-web/
├── public/
│   └── favicon.svg
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Footer.tsx
│   │   │   ├── Logo.tsx
│   │   │   ├── Navbar.tsx
│   │   │   └── RootLayout.tsx
│   │   └── ui/
│   │       ├── badge.tsx
│   │       ├── button.tsx
│   │       └── card.tsx
│   ├── lib/
│   │   ├── constants.ts        # crisis hotlines, app metadata
│   │   └── utils.ts            # `cn` helper
│   ├── pages/
│   │   ├── About.tsx
│   │   ├── Dashboard.tsx       # placeholder for PR B
│   │   ├── Home.tsx
│   │   ├── Resources.tsx
│   │   └── Solution.tsx
│   ├── App.tsx
│   ├── index.css               # Tailwind layers + design tokens
│   └── main.tsx
├── index.html
├── package.json
├── tailwind.config.js
├── tsconfig.app.json
├── vite.config.ts
└── vercel.json
```

## Roadmap

- **PR A** *(this PR)* — scaffold, design system, landing pages
- **PR B** — typed FastAPI client (generated from `/openapi.json`),
  check-in form, today / trends / history tabs, crisis banner,
  Recharts visualisations
- **PR C** — mobile QA, Framer Motion polish, Vercel deploy, README
  update + `run.sh` toggle for legacy Streamlit dashboard
