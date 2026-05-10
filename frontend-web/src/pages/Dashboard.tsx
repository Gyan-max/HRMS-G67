import { Link } from "react-router-dom";
import { Wrench } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

/**
 * Dashboard placeholder — the real check-in form, today's assessment, trends,
 * history, and crisis banner are wired up in PR B (typed FastAPI client +
 * Recharts charts). For now we link out to the Streamlit dashboard which
 * still has full functionality.
 */
export default function Dashboard() {
  const streamlitUrl =
    import.meta.env.VITE_STREAMLIT_URL ?? "http://localhost:8501";

  return (
    <div className="container space-y-10 py-16">
      <section>
        <div className="eyebrow">Dashboard</div>
        <h1 className="mt-3 font-display text-4xl font-extrabold sm:text-5xl">
          Your check-in lives here.
        </h1>
        <p className="mt-5 max-w-2xl text-base text-muted-foreground sm:text-lg">
          The new React dashboard — typed API client, Recharts visualisations,
          form validation, and the live crisis banner — ships in the next PR.
        </p>
      </section>

      <Card className="border-brand-amber/30 bg-brand-amber/[0.04]">
        <CardContent className="flex flex-col gap-6 p-8 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-amber/15 text-brand-amber">
              <Wrench className="h-5 w-5" />
            </div>
            <div>
              <Badge variant="warning">Coming in PR B</Badge>
              <h3 className="mt-3 font-display text-xl font-semibold">
                Use the Streamlit dashboard while we wire up React parity.
              </h3>
              <p className="mt-2 text-sm text-muted-foreground">
                The legacy Streamlit dashboard is still fully functional and
                remains the source of truth for live check-ins, trends, and
                history.
              </p>
            </div>
          </div>
          <Button asChild size="lg" variant="secondary">
            <a href={streamlitUrl} target="_blank" rel="noopener noreferrer">
              Open Streamlit dashboard
            </a>
          </Button>
        </CardContent>
      </Card>

      <section className="grid gap-5 md:grid-cols-2">
        <Card>
          <CardContent className="p-7">
            <div className="eyebrow">Already shipping</div>
            <ul className="mt-4 space-y-2.5 text-sm text-foreground/90">
              <li>• Branded landing experience (Home / About / Solution / Resources)</li>
              <li>• Modern dark design system + Tailwind tokens</li>
              <li>• Always-visible footer with crisis hotlines</li>
              <li>• Sticky navbar with active-state highlighting</li>
            </ul>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-7">
            <div className="eyebrow">Up next (PR B)</div>
            <ul className="mt-4 space-y-2.5 text-sm text-foreground/90">
              <li>• Typed FastAPI client (generated from OpenAPI)</li>
              <li>• Check-in form with validation + optimistic UI</li>
              <li>• Today's assessment with crisis banner integration</li>
              <li>• 7-day trends + 30-day history (Recharts)</li>
            </ul>
            <div className="mt-6">
              <Button asChild variant="link" className="px-0">
                <Link to="/solution">Read the pipeline overview →</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
