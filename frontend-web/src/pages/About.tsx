import { Card, CardContent } from "@/components/ui/card";
import { Check, X } from "lucide-react";

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

export default function About() {
  return (
    <div className="container space-y-20 py-16">
      {/* Header */}
      <section>
        <div className="eyebrow">About Sentinel</div>
        <h1 className="mt-3 max-w-3xl font-display text-4xl font-extrabold sm:text-5xl">
          Built around a simple bet: <span className="text-gradient">drift is detectable</span>.
        </h1>
        <p className="mt-5 max-w-2xl text-base text-muted-foreground sm:text-lg">
          Symptoms of depression, anxiety, and burnout typically begin years
          before someone seeks help. Sentinel is an experiment in catching the
          drift early — by reading sleep, mood, social patterns, and journal
          language together, every day.
        </p>
      </section>

      {/* Pillars */}
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

      {/* Will / won't */}
      <section>
        <div className="eyebrow">Design principles</div>
        <h2 className="mt-3 font-display text-3xl font-bold sm:text-4xl">
          What Sentinel will and won't do.
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
    </div>
  );
}
