import { useState } from "react";
import { ChevronDown, ChevronRight, Activity } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Cell,
  LabelList,
} from "recharts";

import type { CheckInResponse } from "@/api/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CrisisBanner } from "./CrisisBanner";

const RISK_COLOR_BY_LEVEL: Record<string, string> = {
  LOW: "#10b981",
  MEDIUM: "#f59e0b",
  HIGH: "#f43f5e",
};

function colorForScore(score: number): string {
  if (score >= 0.65) return "#f43f5e"; // rose
  if (score >= 0.35) return "#f59e0b"; // amber
  return "#10b981"; // emerald
}

interface TodayAssessmentProps {
  result: CheckInResponse;
}

export function TodayAssessment({ result }: TodayAssessmentProps) {
  const {
    risk_level,
    risk_score,
    component_scores,
    recommendation,
    nlp_analysis,
    anomaly_detected,
    dominant_factor,
  } = result;

  const componentEntries = Object.entries(component_scores ?? {}).sort(
    (a, b) => b[1] - a[1],
  );

  const chartData = componentEntries.map(([name, score]) => ({
    name: name.toUpperCase(),
    score: Number(score.toFixed(3)),
    fill: colorForScore(score),
  }));

  const recAccent =
    risk_level === "HIGH"
      ? "border-brand-rose/40 bg-brand-rose/[0.08]"
      : risk_level === "MEDIUM"
        ? "border-brand-amber/40 bg-brand-amber/[0.08]"
        : "border-brand-emerald/40 bg-brand-emerald/[0.08]";

  return (
    <div className="space-y-6">
      <CrisisBanner result={result} />

      {/* Risk badge + key metrics */}
      <Card>
        <CardContent className="p-7">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <p className="eyebrow">Today's assessment</p>
              <div className="flex flex-wrap items-baseline gap-3">
                <h3 className="font-display text-3xl font-bold">
                  Risk level ·{" "}
                  <span style={{ color: RISK_COLOR_BY_LEVEL[risk_level] }}>
                    {risk_level}
                  </span>
                </h3>
                <span className="text-sm text-muted-foreground">
                  · Score {risk_score.toFixed(2)}
                </span>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 md:gap-5">
              <Metric label="Risk level" value={risk_level} />
              <Metric label="Risk score" value={risk_score.toFixed(3)} />
              <Metric
                label="Dominant"
                value={(dominant_factor ?? "n/a").toUpperCase()}
              />
              <Metric label="Anomaly" value={anomaly_detected ? "YES" : "NO"} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Component breakdown */}
      <Card>
        <CardContent className="p-7">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-display text-lg font-semibold">
                Component risk scores
              </h4>
              <p className="mt-1 text-sm text-muted-foreground">
                How each signal contributes to today's score (0 = low risk · 1
                = high risk).
              </p>
            </div>
            <Badge variant="outline">{componentEntries.length} signals</Badge>
          </div>

          <div className="mt-6 h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 10, right: 60, left: 16, bottom: 10 }}
              >
                <CartesianGrid
                  horizontal={false}
                  stroke="rgba(255,255,255,0.06)"
                />
                <XAxis
                  type="number"
                  domain={[0, 1.05]}
                  tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 12 }}
                  stroke="rgba(255,255,255,0.15)"
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  tick={{ fill: "rgba(255,255,255,0.85)", fontSize: 13 }}
                  stroke="rgba(255,255,255,0.15)"
                  tickLine={false}
                  axisLine={false}
                  width={90}
                />
                <ReferenceLine
                  x={0.35}
                  stroke="rgba(245,158,11,0.5)"
                  strokeDasharray="4 4"
                  label={{
                    value: "MEDIUM",
                    position: "top",
                    fill: "#fcd34d",
                    fontSize: 10,
                  }}
                />
                <ReferenceLine
                  x={0.65}
                  stroke="rgba(244,63,94,0.5)"
                  strokeDasharray="4 4"
                  label={{
                    value: "HIGH",
                    position: "top",
                    fill: "#fda4af",
                    fontSize: 10,
                  }}
                />
                <Bar dataKey="score" radius={[6, 6, 6, 6]} barSize={22}>
                  {chartData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.fill} fillOpacity={0.88} />
                  ))}
                  <LabelList
                    dataKey="score"
                    position="right"
                    formatter={(v: unknown) =>
                      typeof v === "number" ? v.toFixed(2) : ""
                    }
                    style={{
                      fill: "rgba(255,255,255,0.85)",
                      fontSize: 12,
                      fontWeight: 500,
                    }}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Recommendation */}
      <Card className={recAccent}>
        <CardContent className="p-6">
          <p className="eyebrow">Recommendation</p>
          <p className="mt-3 text-sm leading-relaxed text-foreground/95">
            {recommendation}
          </p>
        </CardContent>
      </Card>

      {/* NLP analysis (collapsible) */}
      <NlpAnalysisDetails nlp={nlp_analysis} />

      {anomaly_detected && (
        <div className="rounded-2xl border border-brand-amber/35 bg-brand-amber/[0.07] p-5">
          <div className="flex items-start gap-3">
            <Activity className="mt-0.5 h-5 w-5 shrink-0 text-brand-amber" />
            <p className="text-sm leading-relaxed text-foreground/90">
              <strong className="text-brand-amber">
                Behavioural anomaly detected
              </strong>{" "}
              — your recent patterns deviate significantly from your
              established baseline. This doesn't necessarily mean something is
              wrong, but it's worth reflecting on recent changes.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-1.5 font-display text-lg font-semibold text-foreground">
        {value}
      </p>
    </div>
  );
}

function NlpAnalysisDetails({
  nlp,
}: {
  nlp: CheckInResponse["nlp_analysis"];
}) {
  const [open, setOpen] = useState(false);
  const noJournal = nlp?.status === "no_journal";

  return (
    <Card>
      <CardContent className="p-0">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="flex w-full items-center justify-between p-6 text-left transition-colors hover:bg-white/[0.02]"
          aria-expanded={open}
        >
          <div>
            <h4 className="font-display text-lg font-semibold">
              NLP journal analysis
            </h4>
            <p className="mt-1 text-sm text-muted-foreground">
              {noJournal
                ? "No journal text was provided for this check-in."
                : "Sentiment label, confidence, and linguistic markers."}
            </p>
          </div>
          {open ? (
            <ChevronDown className="h-5 w-5 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-5 w-5 text-muted-foreground" />
          )}
        </button>

        {open && !noJournal && (
          <div className="space-y-5 border-t border-white/5 p-6">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Metric
                label="Sentiment"
                value={String(nlp?.sentiment_label ?? "N/A")}
              />
              <Metric
                label="Confidence"
                value={
                  typeof nlp?.sentiment_confidence === "number"
                    ? `${Math.round(nlp.sentiment_confidence * 100)}%`
                    : "N/A"
                }
              />
              <Metric
                label="NLP risk"
                value={
                  typeof nlp?.nlp_risk_score === "number"
                    ? nlp.nlp_risk_score.toFixed(3)
                    : "N/A"
                }
              />
              <Metric
                label="Word count"
                value={String(nlp?.text_length ?? 0)}
              />
            </div>

            <div>
              <p className="eyebrow">Linguistic markers</p>
              <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
                <Metric
                  label="1st-person ratio"
                  value={
                    typeof nlp?.first_person_ratio === "number"
                      ? nlp.first_person_ratio.toFixed(3)
                      : "0.000"
                  }
                />
                <Metric
                  label="Absolutist ratio"
                  value={
                    typeof nlp?.absolutist_ratio === "number"
                      ? nlp.absolutist_ratio.toFixed(3)
                      : "0.000"
                  }
                />
                <Metric
                  label="Neg. emotion ratio"
                  value={
                    typeof nlp?.negative_emotion_ratio === "number"
                      ? nlp.negative_emotion_ratio.toFixed(3)
                      : "0.000"
                  }
                />
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
