import { Card, CardContent } from "@/components/ui/card";
import { Shield } from "lucide-react";

const STEPS = [
  {
    n: 1,
    title: "Inputs",
    body: "Sleep hours, mood (1–10), activity level, social contact count, journal text (optional).",
  },
  {
    n: 2,
    title: "Feature engineering",
    body: "Normalise each signal to a 0–1 risk component; compute rolling deviations from baseline.",
  },
  {
    n: 3,
    title: "NLP analysis",
    body: "Sentiment + linguistic markers — first-person ratio, absolutist language, negative-emotion ratio.",
  },
  {
    n: 4,
    title: "Anomaly detector",
    body: "Isolation Forest flags samples that deviate from the population baseline (per-user is on the roadmap).",
  },
  {
    n: 5,
    title: "Weighted risk score",
    body: "Five components combined with re-normalised weights when NLP or anomaly aren't available.",
  },
  {
    n: 6,
    title: "Safety screen",
    body: "Phrase-based detector for crisis language. If matched, risk is forced to HIGH, no exceptions.",
  },
];

const WEIGHTS = [
  { name: "NLP", pct: 30, color: "bg-brand-indigo" },
  { name: "Sleep", pct: 20, color: "bg-brand-cyan" },
  { name: "Mood", pct: 20, color: "bg-brand-teal" },
  { name: "Social", pct: 15, color: "bg-brand-amber" },
  { name: "Anomaly", pct: 10, color: "bg-brand-rose" },
  { name: "Activity", pct: 5, color: "bg-brand-emerald" },
];

export default function Solution() {
  return (
    <div className="container space-y-20 py-16">
      {/* Header */}
      <section>
        <div className="eyebrow">How Sentinel works</div>
        <h1 className="mt-3 max-w-4xl font-display text-4xl font-extrabold sm:text-5xl">
          From a 60-second check-in to an{" "}
          <span className="text-gradient">explainable risk score</span>.
        </h1>
        <p className="mt-5 max-w-3xl text-base text-muted-foreground sm:text-lg">
          The pipeline is intentionally simple — five signals, one weighted
          blend, and a non-negotiable safety screen. Every step is auditable
          from the dashboard, and every score is visible to the user.
        </p>
      </section>

      {/* Pipeline */}
      <section className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {STEPS.map((s) => (
          <Card key={s.n}>
            <CardContent className="p-6">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-grad-brand font-display text-sm font-bold text-white">
                {s.n}
              </div>
              <h4 className="mt-4 font-display text-base font-semibold">
                {s.title}
              </h4>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {s.body}
              </p>
            </CardContent>
          </Card>
        ))}
      </section>

      {/* Weights */}
      <section>
        <div className="eyebrow">Risk weights</div>
        <h2 className="mt-3 font-display text-3xl font-bold sm:text-4xl">
          How the components combine.
        </h2>
        <p className="mt-4 max-w-3xl text-muted-foreground">
          Default weights (tuned on synthetic data — not a clinical instrument).
          When NLP or anomaly signals aren't available, the remaining weights
          re-normalise to 1.0 so users without journals or short history aren't
          silently under-scored.
        </p>

        <Card className="mt-8">
          <CardContent className="p-7">
            <div className="space-y-4">
              {WEIGHTS.map((w) => (
                <div key={w.name}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-foreground/90">
                      {w.name}
                    </span>
                    <span className="text-muted-foreground">{w.pct}%</span>
                  </div>
                  <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-white/[0.04]">
                    <div
                      className={`h-full ${w.color} rounded-full transition-all`}
                      style={{ width: `${w.pct}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Safety screen */}
      <section>
        <Card className="border-brand-rose/30 bg-brand-rose/[0.04]">
          <CardContent className="p-8">
            <div className="flex items-center gap-3 text-brand-rose">
              <Shield className="h-6 w-6" />
              <h4 className="font-display text-lg font-semibold">
                The safety screen — non-negotiable
              </h4>
            </div>
            <p className="mt-4 max-w-3xl text-sm leading-relaxed text-foreground/90">
              Before any blending happens, the journal text is checked for
              phrases associated with active suicidal ideation, self-harm, or
              planning. The list includes negation handling so{" "}
              <em className="text-muted-foreground">
                "I would never want to die"
              </em>{" "}
              doesn't trigger. If a phrase matches, the risk level is forced
              to <strong className="text-brand-rose">HIGH</strong> regardless
              of how good the sleep / mood / social numbers look, and crisis
              hotlines surface immediately above the assessment. The matched
              phrases are logged but never echoed back to the user.
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
