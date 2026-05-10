import { AlertTriangle } from "lucide-react";
import type { CheckInResponse } from "@/api/types";

interface CrisisBannerProps {
  result: Pick<CheckInResponse, "risk_level" | "safety_override">;
}

/**
 * Crisis banner — surfaces above the assessment when the safety screen
 * forces HIGH risk OR when the weighted score lands in HIGH territory.
 *
 * Copy and hotline numbers MUST stay in sync with `_render_assessment` in
 * `frontend/dashboard.py` and the recommendation text in
 * `backend/safety_screen.py`. Never echo the user's matched phrases.
 */
export function CrisisBanner({ result }: CrisisBannerProps) {
  const safetyOverride = !!result.safety_override;
  const isHigh = result.risk_level === "HIGH";

  if (!safetyOverride && !isHigh) return null;

  const heading = safetyOverride
    ? "We're concerned about what you've shared"
    : "Your check-in indicates HIGH risk — please reach out";

  const opening = safetyOverride
    ? "Your journal entry contains language that suggests you may be struggling with thoughts of self-harm. You are not alone, and help is available right now."
    : "Several signals from your check-in suggest you may be struggling. Please consider reaching out to someone you trust or a crisis line today.";

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="rounded-2xl border border-brand-rose/40 bg-brand-rose/10 p-7 shadow-[0_25px_60px_-30px_rgba(244,63,94,0.55)]"
    >
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-rose/20 text-brand-rose">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <div className="flex-1">
          <h3 className="font-display text-xl font-bold text-brand-rose">
            {heading}
          </h3>
          <p className="mt-3 text-sm leading-relaxed text-foreground/95">
            {opening}
          </p>
          <ul className="mt-5 space-y-1.5 text-sm text-foreground/95">
            <li>
              <span aria-hidden>🇮🇳 </span>
              <strong>iCall</strong> — 9152987821 (Mon–Sat, 8am–10pm)
            </li>
            <li>
              <span aria-hidden>🇮🇳 </span>
              <strong>AASRA</strong> — 9820466726 (24/7)
            </li>
            <li>
              <span aria-hidden>🇺🇸 </span>
              <strong>988 Suicide &amp; Crisis Lifeline</strong> — call or text 988
            </li>
            <li>
              <span aria-hidden>🇬🇧 </span>
              <strong>Samaritans</strong> — 116 123
            </li>
          </ul>
          <p className="mt-5 text-sm font-semibold text-brand-rose">
            If you are in immediate danger, please call your local emergency
            services.
          </p>
        </div>
      </div>
    </div>
  );
}
