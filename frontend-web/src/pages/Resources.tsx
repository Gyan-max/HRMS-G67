import { Card, CardContent } from "@/components/ui/card";
import { HOTLINES } from "@/lib/constants";
import { ExternalLink, AlertTriangle, Stethoscope } from "lucide-react";

const REACH_OUT_TODAY = [
  "You're having thoughts of suicide or self-harm",
  "You feel like a burden to others",
  "You're using substances to cope",
  "You're isolating from people who care about you",
  "You can't sleep, or you're sleeping all day",
];

const WORTH_PROFESSIONAL = [
  "Persistent low mood for two weeks or more",
  "Loss of interest in things you used to enjoy",
  "Physical symptoms with no clear cause",
  "Anxiety that's interfering with daily life",
  "Trouble concentrating or making decisions",
];

export default function Resources() {
  return (
    <div className="container space-y-20 py-16">
      {/* Header */}
      <section>
        <div className="eyebrow">Resources</div>
        <h1 className="mt-3 max-w-3xl font-display text-4xl font-extrabold sm:text-5xl">
          If you need someone to talk to{" "}
          <span className="text-gradient">right now</span>.
        </h1>
        <p className="mt-5 max-w-2xl text-base text-muted-foreground sm:text-lg">
          You don't need to be in immediate danger to call a crisis line.
          They are trained to listen — even if you're "just" overwhelmed,
          isolated, or scared.
        </p>
      </section>

      {/* Hotlines */}
      <section className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {HOTLINES.map((h) => (
          <Card key={h.name}>
            <CardContent className="p-6">
              <div className="flex items-center gap-2">
                <span className="text-lg" aria-hidden>
                  {h.flag}
                </span>
                <h4 className="font-display text-base font-semibold">
                  {h.name}
                </h4>
              </div>
              <div className="mt-4 font-display text-2xl font-bold text-gradient">
                {h.number}
              </div>
              <p className="mt-3 text-sm text-muted-foreground">{h.note}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      {/* When to reach out */}
      <section>
        <div className="eyebrow">When to reach out</div>
        <h2 className="mt-3 font-display text-3xl font-bold sm:text-4xl">
          Signals worth taking seriously.
        </h2>

        <div className="mt-10 grid gap-5 md:grid-cols-2">
          <Card>
            <CardContent className="p-7">
              <div className="flex items-center gap-2 text-brand-rose">
                <AlertTriangle className="h-5 w-5" />
                <h4 className="font-display text-base font-semibold">
                  Reach out today if any of these are true
                </h4>
              </div>
              <ul className="mt-4 space-y-2.5 text-sm text-foreground/90">
                {REACH_OUT_TODAY.map((line) => (
                  <li key={line} className="flex gap-2">
                    <span className="text-brand-rose">•</span>
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-7">
              <div className="flex items-center gap-2 text-brand-cyan">
                <Stethoscope className="h-5 w-5" />
                <h4 className="font-display text-base font-semibold">
                  Worth checking in with a professional
                </h4>
              </div>
              <ul className="mt-4 space-y-2.5 text-sm text-foreground/90">
                {WORTH_PROFESSIONAL.map((line) => (
                  <li key={line} className="flex gap-2">
                    <span className="text-brand-cyan">•</span>
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* International */}
      <section>
        <Card>
          <CardContent className="flex flex-col items-start gap-4 p-7 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h4 className="font-display text-base font-semibold">
                International directory
              </h4>
              <p className="mt-2 text-sm text-muted-foreground">
                Use IASP's directory to find a crisis centre in your country.
              </p>
            </div>
            <a
              href="https://www.iasp.info/resources/Crisis_Centres/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-white/[0.07]"
            >
              IASP — Crisis centres around the world
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
