import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] transition-colors",
  {
    variants: {
      variant: {
        default:
          "border border-brand-cyan/30 bg-brand-cyan/10 text-brand-cyan",
        muted:
          "border border-white/10 bg-white/[0.04] text-muted-foreground",
        success:
          "border border-brand-emerald/30 bg-brand-emerald/10 text-brand-emerald",
        warning:
          "border border-brand-amber/30 bg-brand-amber/10 text-brand-amber",
        danger:
          "border border-brand-rose/30 bg-brand-rose/10 text-brand-rose",
        outline:
          "border border-white/15 bg-transparent text-foreground/80",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
