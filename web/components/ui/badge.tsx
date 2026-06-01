import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";

const badgeVariants = cva(
  "inline-flex items-center rounded-lg px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default:
          "bg-accent-muted text-accent-light border border-accent/20",
        secondary:
          "bg-surface-raised text-text-secondary border border-surface-border/50",
        success:
          "bg-success-muted text-success border border-success/20",
        warning:
          "bg-warning-muted text-warning border border-warning/20",
        danger:
          "bg-danger-muted text-danger border border-danger/20",
        outline:
          "border border-surface-border text-text-tertiary",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
