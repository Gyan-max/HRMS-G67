import { Card, CardContent } from "@/components/ui/card";
import { Check, X, Brain, Code2, LayoutDashboard, BookOpen, Database, FlaskConical } from "lucide-react";

const PILLARS = [
  {
    title: "Mission",
    body: "Build a simple, honest companion that surfaces early mental-health drift before it becomes a crisis — and shows the user exactly why it's worried.",
  },
  {
    title: "Vision",
    body: "A future where everyone has access to a private, transparent, daily mental-health signal — not as a replacement for professional care, but as a bridge to it.",
  },
  {
    title: "Ethos",
    body: "We optimise for safety over polish, transparency over wow-factor, and explainability over magic. We never echo a user's crisis language back to them.",
  },
];

const WILL = [
  "Surface crisis hotlines instantly when self-harm language is detected",
  "Show every component score and the dominant factor behind a risk level",
  "Re-normalise weights when journals or anomaly history are missing",
  "Treat synthetic-data scores as research signal, not a clinical instrument",
];

const WONT = [
  "Replace therapy, medication, or professional clinical judgement",
  "Echo a user's matched crisis phrases back to them in any way",
  "Sell, share, or monetise user data — full stop",
  "Pretend a single number from a 60-second check-in is a diagnosis",
];

const TEAM = [
  {
    name:  "Ustav Kumar",
    role:  "Project Lead & Backend Engineer",
    Icon:  Code2,
    color: "text-brand-indigo",
    bg:    "bg-brand-indigo/10",
    contributions: [
      "Led overall system design and coordinated the team's work",
      "Built the FastAPI backend — all API endpoints, database layer, and startup pipeline",
      "Implemented the weighted risk scoring engine with personalized insight generation",
      "Wired all ML components into the end-to-end prediction pipeline",
      "Set up CORS configuration, structured logging, and deployment scripts",
    ],
  },
  {
    name:  "Vikash Kumar",
    role:  "Machine Learning Engineer",
    Icon:  Brain,
    color: "text-brand-cyan",
    bg:    "bg-brand-cyan/10",
    contributions: [
      "Built and trained the XGBoost risk classifier (LOW / MEDIUM / HIGH)",
      "Replaced binary sentiment with a 7-class emotion detection NLP model",
      "Implemented SHAP explainability so users see which features drove their score",
      "Added 5-fold cross-validation to produce honest generalisation metrics",
      "Designed the 60% rule-based / 40% ML score blending strategy",
    ],
  },
  {
    name:  "Vikash Kumar",
    role:  "NLP, Research & Clinical Logic",
    Icon:  FlaskConical,
    color: "text-brand-amber",
    bg:    "bg-brand-amber/10",
    contributions: [
      "Researched PHQ-9 and GAD-7 clinical scales to align the training data",
      "Built the safety screen — 75+ crisis phrases, regex patterns, negation detection",
      "Designed the early-warning pattern detector (mood freefall, sleep debt, isolation)",
      "Generated the 5,000-sample synthetic dataset using clinical feature distributions",
      "Wrote the personalized observation text that cites the user's real numbers",
    ],
  },
  {
    name:  "Vikash Kumar",
    role:  "Data Engineering & Anomaly Detection",
    Icon:  Database,
    color: "text-brand-rose",
    bg:    "bg-brand-rose/10",
    contributions: [
      "Designed and implemented the 24-feature behavioral engineering pipeline",
      "Built streak detectors (consecutive low-mood days, sleep deficit, isolation)",
      "Implemented velocity features to catch accelerating deterioration",
      "Built the per-user Isolation Forest anomaly detector — personal vs population model",
      "Designed the SQLite database schema and all data ingestion helpers",
    ],
  },
  {
    name:  "Vinay Kumar",
    role:  "Frontend & UI/UX Design",
    Icon:  LayoutDashboard,
    color: "text-brand-teal",
    bg:    "bg-brand-teal/10",
    contributions: [
      "Designed and built the complete React + TypeScript web application",
      "Created the interactive dashboard — trend charts, check-in form, history log",
      "Implemented the dark-theme design system with Tailwind CSS and glass-morphism cards",
      "Built the component score breakdown, SHAP display, and early-warning cards in the UI",
      "Ensured mobile responsiveness, skeleton loaders, and accessible UI across all pages",
    ],
  },
];

export default function About() {
  return (
    <div className="container space-y-20 py-16">

      {/* ── Header ── */}
      <section>
        <div className="eyebrow">About Sentinel</div>
        <h1 className="mt-3 max-w-3xl font-display text-4xl font-extrabold sm:text-5xl">
          Built around a simple bet:{" "}
          <span className="text-gradient">drift is detectable</span>.
        </h1>
        <p className="mt-5 max-w-2xl text-base text-muted-foreground sm:text-lg">
          Symptoms of depression, anxiety, and burnout typically begin years
          before someone seeks help. Sentinel is an experiment in catching the
          drift early — by reading sleep, mood, social patterns, and journal
          language together, every day.
        </p>
      </section>

      {/* ── Mission / Vision / Ethos ── */}
      <section className="grid gap-5 md:grid-cols-3">
        {PILLARS.map((p) => (
          <Card key={p.title}>
            <CardContent className="p-7">
              <div className="eyebrow">{p.title}</div>
              <p className="mt-4 text-sm leading-relaxed text-foreground/90">
                {p.body}
              </p>
            </CardContent>
          </Card>
        ))}
      </section>

      {/* ── Will / Won't ── */}
      <section>
        <div className="eyebrow">Design principles</div>
        <h2 className="mt-3 font-display text-3xl font-bold sm:text-4xl">
          What Sentinel will and won&apos;t do.
        </h2>

        <div className="mt-10 grid gap-5 md:grid-cols-2">
          <Card>
            <CardContent className="p-7">
              <div className="flex items-center gap-2 text-brand-emerald">
                <Check className="h-5 w-5" />
                <span className="font-display text-base font-semibold">
                  Sentinel will
                </span>
              </div>
              <ul className="mt-4 space-y-2.5 text-sm text-foreground/90">
                {WILL.map((line) => (
                  <li key={line} className="flex gap-2">
                    <span className="text-brand-emerald">•</span>
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-7">
              <div className="flex items-center gap-2 text-brand-rose">
                <X className="h-5 w-5" />
                <span className="font-display text-base font-semibold">
                  Sentinel will not
                </span>
              </div>
              <ul className="mt-4 space-y-2.5 text-sm text-foreground/90">
                {WONT.map((line) => (
                  <li key={line} className="flex gap-2">
                    <span className="text-brand-rose">•</span>
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* ── Team ── */}
      <section>
        <div className="eyebrow">The team</div>
        <h2 className="mt-3 font-display text-3xl font-bold sm:text-4xl">
          Meet the five people who built Sentinel.
        </h2>
        <p className="mt-4 max-w-2xl text-muted-foreground">
          Sentinel was built as a final-year HRMS project by a five-person team
          bringing together backend engineering, machine learning, clinical research,
          data engineering, and frontend design. Project reference:{" "}
          <span className="font-medium text-foreground">HRMS-G67</span>.
        </p>

        {/* Row 1: 3 cards */}
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {TEAM.slice(0, 3).map(({ name, role, Icon, color, bg, contributions }, i) => (
            <Card key={`${name}-${i}`} className="flex flex-col">
              <CardContent className="flex flex-1 flex-col p-7">
                <div className={`flex h-14 w-14 items-center justify-center rounded-2xl ${bg}`}>
                  <Icon className={`h-7 w-7 ${color}`} />
                </div>
                <div className="mt-5">
                  <h3 className="font-display text-xl font-bold">{name}</h3>
                  <p className={`mt-1 text-sm font-semibold ${color}`}>{role}</p>
                </div>
                <ul className="mt-5 flex-1 space-y-2">
                  {contributions.map((c) => (
                    <li key={c} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <span className={`mt-1 shrink-0 text-xs ${color}`}>▸</span>
                      <span>{c}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Row 2: 2 cards centred */}
        <div className="mt-6 grid gap-6 md:grid-cols-2 lg:mx-auto lg:max-w-3xl">
          {TEAM.slice(3).map(({ name, role, Icon, color, bg, contributions }, i) => (
            <Card key={`${name}-${i + 3}`} className="flex flex-col">
              <CardContent className="flex flex-1 flex-col p-7">
                <div className={`flex h-14 w-14 items-center justify-center rounded-2xl ${bg}`}>
                  <Icon className={`h-7 w-7 ${color}`} />
                </div>
                <div className="mt-5">
                  <h3 className="font-display text-xl font-bold">{name}</h3>
                  <p className={`mt-1 text-sm font-semibold ${color}`}>{role}</p>
                </div>
                <ul className="mt-5 flex-1 space-y-2">
                  {contributions.map((c) => (
                    <li key={c} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <span className={`mt-1 shrink-0 text-xs ${color}`}>▸</span>
                      <span>{c}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* ── Project info ── */}
      <section>
        <Card>
          <CardContent className="flex flex-col items-start gap-5 p-8 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="eyebrow">Project info</div>
              <h3 className="mt-2 font-display text-xl font-bold">
                HRMS-G67 — Behavioral Health Risk Monitor
              </h3>
              <p className="mt-2 max-w-xl text-sm text-muted-foreground">
                An educational and research prototype exploring early mental-health
                signal detection. Built with FastAPI, XGBoost, HuggingFace
                Transformers, React, and Tailwind CSS. Not a clinical diagnostic tool.
              </p>
            </div>
            <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-medium text-muted-foreground shrink-0">
              <BookOpen className="h-4 w-4" />
              HRMS-G67
            </div>
          </CardContent>
        </Card>
      </section>

    </div>
  );
}
