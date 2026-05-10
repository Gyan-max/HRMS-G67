interface LogoProps {
  className?: string;
}

/**
 * Sentinel logo — shield + upward-trending pulse line, gradient cyan→indigo.
 * Inline SVG so we don't need an asset pipeline.
 */
export function Logo({ className }: LogoProps) {
  return (
    <svg
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Sentinel logo"
      role="img"
      className={className}
    >
      <defs>
        <linearGradient id="sg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#22d3ee" />
          <stop offset="100%" stopColor="#6366f1" />
        </linearGradient>
      </defs>
      <path
        d="M32 4 L56 14 L56 30 C56 46 44 56 32 60 C20 56 8 46 8 30 L8 14 Z"
        fill="url(#sg)"
        opacity="0.18"
        stroke="url(#sg)"
        strokeWidth="2.2"
        strokeLinejoin="round"
      />
      <path
        d="M14 34 L22 34 L26 24 L32 44 L38 28 L42 34 L50 34"
        fill="none"
        stroke="url(#sg)"
        strokeWidth="3.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
