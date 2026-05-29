import { Link } from "react-router-dom";
import {
  Shield,
  BarChart3,
  Brain,
  Scale,
  Siren,
  Search,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const PROBLEM_STATS = [
  { value: "1 in 8",  label: "people globally live with a mental disorder",         source: "WHO, 2022" },
  { value: "75%",     label: "of mental-health conditions emerge before age 25",     source: "NIH" },
  { value: "8–10 yr", label: "average gap between symptom onset and treatment",      source: "NIMH" },
  { value: "4th",     label: "leading cause of death among 15–29 yr olds (suicide)", source: "WHO" },
];

const PIPELINE_STEPS = [
  { n: 1, title: "Daily check-in",    body: "Sleep, mood (1–10), activity, social contact, optional journal — under 60 seconds." },
  { n: 2, title: "NLP & anomaly",     body: "Journal sentiment, linguistic markers, and per-window deviation from baseline." },
  { n: 3, title: "Risk engine",       body: "Weighted blend of five components plus a phrase-based safety screen for crisis language." },
  { n: 4, title: "Actionable result", body: "Risk level, dominant factor, plain-language guidance — crisis resources when needed." },
];

const VALUE_PROPS = [
  { Icon: Shield,   title: "Safety first",       body: "A phrase-based screen for self-harm language unconditionally forces HIGH risk and surfaces crisis hotlines." },
  { Icon: BarChart3, title: "Holistic signal",   body: "Five weighted components — never a single black-box number. You see exactly what drove the score." },
  { Icon: Brain,    title: "Contextual NLP",     body: "Sentiment plus linguistic markers (1st-person ratio, absolutist language, negative-emotion ratio)." },
  { Icon: Scale,    title: "Adaptive scoring",   body: "Weights re-normalise when journals or anomaly history aren't available — no silent under-scoring." },
  { Icon: Siren,    title: "Crisis-ready",       body: "Helplines surface immediately on HIGH or any safety override, never buried behind an expander." },
  { Icon: Search,   title: "Explainable",        body: "Every component score, the dominant factor, and the recommendation are all visible to the user." },
];

const HERO_BULLETS = [
  "Daily check-in in under 60 seconds",
  "Five weighted signals · explainable",
  "Crisis resources surface instantly",
];

export default function Home() {
  return (
    <div className="container space-y-28 py-16">

      {/* ── HERO ── */}
      <section className="animate-fade-in-up">
        <Card className="overflow-hidden">
          <CardContent className="relative px-8 py-16 sm:px-14 sm:py-20 md:px-20">
            {/* Dot grid overlay */}
            <div className="bg-grid-dots pointer-events-none absolute inset-0 rounded-2xl opacity-100" />

            {/* Glow orbs */}
            <div className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-brand-indigo/20 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-20 -left-20 h-72 w-72 rounded-full bg-brand-cyan/15 blur-3xl" />

            <div className="relative">
              <Badge variant="default">
                <Shield className="h-3.5 w-3.5" />
                Sentinel · v0.1
              </Badge>

              <h1 className="mt-6 max-w-4xl font-display text-4xl font-extrabold leading-[1.05] sm:text-5xl md:text-6xl">
                Catch the <span className="text-gradient">drift</span>, not
                just the&nbsp;crisis.
              </h1>

              <p className="mt-6 max-w-2xl text-base leading-relaxed text-muted-foreground sm:text-lg">
                Most mental-health tools react after a crisis. Sentinel reads the
                slow signals — disrupted sleep, fading social contact, journals
                turning bleak — and surfaces them{" "}
                <strong className="text-foreground">before</strong> things
                escalate, with a non-negotiable safety net for crisis language.
              </p>

              <ul className="mt-7 flex flex-wrap gap-x-6 gap-y-2 text-sm">
                {HERO_BULLETS.map((b) => (
                  <li key={b} className="flex items-center gap-2 text-muted-foreground">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-brand-cyan" />
                    {b}
                  </li>
                ))}
              </ul>

              <div className="mt-10 flex flex-wrap gap-3">
                <Button asChild size="lg">
                  <Link to="/dashboard">
                    Start your check-in <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
                <Button asChild size="lg" variant="secondary">
                  <Link to="/solution">How it works</Link>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* ── THE PROBLEM ── */}
      <section>
        <div className="eyebrow">The problem</div>
        <h2 className="mt-3 max-w-3xl font-display text-3xl font-bold sm:text-4xl">
          Mental health doesn&apos;t break overnight — it drifts.
        </h2>
        <p className="mt-4 max-w-3xl text-muted-foreground">
          Symptoms typically begin years before someone seeks help. The
          earliest signals — sleep changes, withdrawal, mood shifts, bleaker
          self-talk — are exactly the kind of patterns a daily journal can
          capture, if something is paying attention.
        </p>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PROBLEM_STATS.map((s) => (
            <Card key={s.label} className="group relative overflow-hidden">
              {/* Subtle gradient accent on hover */}
              <div className="pointer-events-none absolute inset-x-0 -top-px h-px bg-grad-brand opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
              <CardContent className="p-6">
                <div className="font-display text-3xl font-extrabold text-gradient">
                  {s.value}
                </div>
                <p className="mt-3 text-sm leading-snug text-foreground/90">
                  {s.label}
                </p>
                <p className="mt-3 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                  {s.source}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* ── SOLUTION PIPELINE ── */}
      <section>
        <div className="eyebrow">Our solution</div>
        <h2 className="mt-3 max-w-3xl font-display text-3xl font-bold sm:text-4xl">
          Five signals. One score. A safety net that never sleeps.
        </h2>
        <p className="mt-4 max-w-3xl text-muted-foreground">
          Sentinel reads sleep, mood, activity, social contact, and journal
          language together — then blends them into one weighted score with
          an unconditional crisis screen layered on top.
        </p>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PIPELINE_STEPS.map((step) => (
            <Card key={step.n} className="relative overflow-hidden">
              <CardContent className="p-6">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-grad-brand font-display text-sm font-bold text-white shadow-[0_6px_20px_-6px_rgba(99,102,241,0.5)]">
                  {step.n}
                </div>
                <h4 className="mt-4 font-display text-base font-semibold">
                  {step.title}
                </h4>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {step.body}
                </p>
              </CardContent>
              {/* Step connector line (decorative) */}
              <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-white/5 to-transparent" />
            </Card>
          ))}
        </div>
      </section>

      {/* ── VALUE PROPS ── */}
      <section>
        <div className="eyebrow">Why Sentinel</div>
        <h2 className="mt-3 max-w-3xl font-display text-3xl font-bold sm:text-4xl">
          Designed to be honest, transparent, and safe-by-default.
        </h2>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {VALUE_PROPS.map(({ Icon, title, body }) => (
            <Card key={title} className="group">
              <CardContent className="p-6">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 text-brand-cyan transition-colors duration-200 group-hover:bg-brand-cyan/10">
                  <Icon className="h-5 w-5" />
                </div>
                <h4 className="mt-4 font-display text-base font-semibold">
                  {title}
                </h4>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {body}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* ── CTA STRIP ── */}
      <section>
        <Card className="overflow-hidden">
          <CardContent className="relative flex flex-col items-start gap-6 p-8 sm:flex-row sm:items-center sm:justify-between">
            <div className="pointer-events-none absolute -right-10 -top-10 h-48 w-48 rounded-full bg-brand-indigo/15 blur-2xl" />
            <div className="relative">
              <h3 className="font-display text-2xl font-bold">
                Ready to try a check-in?
              </h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Takes under a minute. Your data stays in the local database.
              </p>
            </div>
            <Button asChild size="lg" className="relative shrink-0">
              <Link to="/dashboard">
                Open the dashboard <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
