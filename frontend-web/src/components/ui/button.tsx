import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

/**
 * Sentinel button — shadcn-style API with a brand gradient `primary` variant.
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-semibold ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:
          "bg-grad-brand text-white shadow-[0_10px_25px_-12px_rgba(99,102,241,0.6)] hover:opacity-95 hover:scale-[1.02]",
        secondary:
          "border border-white/10 bg-white/[0.04] text-foreground hover:bg-white/[0.07]",
        ghost: "text-foreground/80 hover:text-foreground hover:bg-white/[0.05]",
        link: "text-brand-cyan underline-offset-4 hover:underline",
        destructive: "bg-destructive text-destructive-foreground hover:opacity-95",
      },
      size: {
        sm: "h-9 px-4",
        md: "h-11 px-5",
        lg: "h-12 px-7 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
