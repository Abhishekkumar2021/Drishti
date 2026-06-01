import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-gradient-to-r from-accent to-accent-dark text-white shadow-glow-sm hover:shadow-glow hover:from-accent-light hover:to-accent active:scale-[0.98]",
        secondary:
          "bg-surface-raised/80 text-text-secondary border border-surface-border/50 backdrop-blur-sm hover:bg-surface-elevated hover:text-text-primary hover:border-surface-border-light active:scale-[0.98]",
        outline:
          "border border-surface-border/50 bg-transparent text-text-secondary backdrop-blur-sm hover:bg-surface-raised/50 hover:text-text-primary hover:border-accent/30 active:scale-[0.98]",
        ghost:
          "text-text-tertiary hover:text-text-primary hover:bg-surface-raised/50 active:scale-[0.98]",
        destructive:
          "bg-danger/20 text-danger border border-danger/30 hover:bg-danger/30 hover:border-danger/50 active:scale-[0.98]",
        link: "text-accent-light underline-offset-4 hover:underline hover:text-accent",
        glow: "bg-gradient-to-r from-accent via-primary to-accent text-white shadow-glow animate-gradient bg-[length:200%_200%] hover:shadow-glow-lg active:scale-[0.98]",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 rounded-lg px-3 text-xs",
        lg: "h-12 rounded-xl px-6 text-base",
        xl: "h-14 rounded-2xl px-8 text-lg",
        icon: "h-10 w-10",
        "icon-sm": "h-8 w-8 rounded-lg",
        "icon-lg": "h-12 w-12",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
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
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
