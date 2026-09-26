/**
 * components/ui/Button.tsx
 * ========================
 * Reusable button component with multiple variants and sizes.
 */

import React from "react";
import { cn } from "@/lib/utils";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "ghost"
  | "danger"
  | "outline";
export type ButtonSize = "xs" | "sm" | "md" | "lg";

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-blue-600 hover:bg-blue-500 text-white border border-blue-500 shadow-sm",
  secondary:
    "bg-slate-700 hover:bg-slate-600 text-slate-100 border border-slate-600",
  ghost:
    "bg-transparent hover:bg-slate-800 text-slate-300 hover:text-white border border-transparent hover:border-slate-700",
  danger:
    "bg-rose-700 hover:bg-rose-600 text-white border border-rose-600",
  outline:
    "bg-transparent hover:bg-slate-800 text-slate-300 border border-slate-600 hover:border-slate-500",
};

const sizeClasses: Record<ButtonSize, string> = {
  xs: "text-xs px-2 py-1 rounded",
  sm: "text-sm px-3 py-1.5 rounded-md",
  md: "text-sm px-4 py-2 rounded-md",
  lg: "text-base px-5 py-2.5 rounded-lg",
};

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  leftIcon,
  rightIcon,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 font-medium transition-all duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1 focus-visible:ring-offset-slate-900",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <svg
          className="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      ) : (
        leftIcon && <span aria-hidden="true">{leftIcon}</span>
      )}
      {children}
      {!loading && rightIcon && <span aria-hidden="true">{rightIcon}</span>}
    </button>
  );
}

export default Button;
