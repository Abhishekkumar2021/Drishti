"use client";

import * as React from "react";
import { cn } from "@/lib/cn";

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number;
  max?: number;
  showLabel?: boolean;
  size?: "sm" | "md" | "lg";
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, max = 100, showLabel = false, size = "md", ...props }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

    return (
      <div
        ref={ref}
        className={cn("w-full", className)}
        {...props}
      >
        <div
          className={cn(
            "w-full rounded-full bg-surface-border overflow-hidden",
            size === "sm" && "h-1",
            size === "md" && "h-1.5",
            size === "lg" && "h-2"
          )}
        >
          <div
            className="h-full rounded-full bg-accent transition-all duration-300 ease-out"
            style={{ width: `${percentage}%` }}
          />
        </div>
        {showLabel && (
          <p className="mt-1 text-xs text-text-muted text-right">
            {Math.round(percentage)}%
          </p>
        )}
      </div>
    );
  }
);
Progress.displayName = "Progress";

export { Progress };
