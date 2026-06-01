import * as React from "react";
import { cn } from "@/lib/cn";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, icon, iconRight, ...props }, ref) => {
    return (
      <div className="relative">
        {icon && (
          <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none">
            {icon}
          </div>
        )}
        <input
          type={type}
          className={cn(
            "flex h-11 w-full rounded-xl bg-surface px-4 py-2.5 text-sm text-text-primary",
            "placeholder:text-text-muted",
            "border border-surface-border",
            "focus:border-surface-border-light focus:outline-none focus:ring-1 focus:ring-surface-border-light",
            "transition-all duration-150",
            "disabled:cursor-not-allowed disabled:opacity-50",
            icon && "pl-11",
            iconRight && "pr-11",
            className
          )}
          ref={ref}
          {...props}
        />
        {iconRight && (
          <div className="absolute right-3.5 top-1/2 -translate-y-1/2 text-text-muted">
            {iconRight}
          </div>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export { Input };
