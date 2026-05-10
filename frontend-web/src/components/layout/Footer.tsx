import { FOOTER_HOTLINES } from "@/lib/constants";

/**
 * Always-visible site footer.
 *
 * The crisis hotline numbers must match the safety screen's numbers exactly —
 * they are referenced in the backend's recommendation text on HIGH risk.
 */
export function Footer() {
  return (
    <footer className="mt-24 border-t border-white/5 bg-background/40 backdrop-blur-md">
      <div className="container grid gap-10 py-12 md:grid-cols-3">
        <div>
          <div className="eyebrow">Sentinel</div>
          <p className="mt-3 max-w-prose text-sm text-muted-foreground">
            Early mental-health signal detection through daily check-ins,
            NLP analysis, and a safety screen that surfaces crisis resources
            immediately when needed.
          </p>
        </div>

        <div>
          <div className="eyebrow">Crisis hotlines</div>
          <ul className="mt-3 space-y-1.5 text-sm text-muted-foreground">
            {FOOTER_HOTLINES.map((h) => (
              <li key={h.label}>
                <strong className="text-foreground">{h.label}</strong> —{" "}
                {h.number}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <div className="eyebrow">About</div>
          <ul className="mt-3 space-y-1.5 text-sm text-muted-foreground">
            <li>Educational &amp; research use only</li>
            <li>Not a clinical diagnostic tool</li>
            <li>Built on FastAPI · React · Tailwind · XGBoost · DistilBERT</li>
          </ul>
        </div>
      </div>

      <div className="border-t border-white/5">
        <div className="container py-6 text-xs leading-relaxed text-muted-foreground">
          <strong className="text-foreground">Disclaimer.</strong> Sentinel is
          for educational and research purposes only and is{" "}
          <strong className="text-foreground">not</strong> a clinical
          diagnostic tool. It does not provide medical advice, diagnosis, or
          treatment. If you are in crisis or experiencing a mental-health
          emergency, please contact a qualified professional or your local
          emergency services immediately.
        </div>
      </div>
    </footer>
  );
}
