/**
 * components/ui/Button.tsx
 * ========================
 * Standardized institutional button component.
 *
 * Implements:
 * - Variants: primary, secondary, tertiary, destructive (danger), ghost, outline
 * - Sizes: xs, sm, md, lg, icon (square touch target)
 * - States: hover, active, focus-visible ring, disabled, loading spinner
 * - Theme-calibrated semantic tokens for Light and Dark modes
 * - Accessibility: aria-busy, aria-disabled, enforcement of accessible names for icon-only buttons
 */

import React from "react";
import { cn } from "@/lib/utils";
import { SpinnerIcon } from "./Icons";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "tertiary"
  | "ghost"
  | "danger"
  | "destructive"
  | "outline";

export type ButtonSize = "xs" | "sm" | "md" | "lg" | "icon";

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-[var(--action-primary)] hover:bg-[var(--action-primary-hover)] active:bg-[var(--action-active)] text-white border border-transparent shadow-xs active:translate-y-[0.5px]",
  secondary:
    "bg-[var(--action-secondary)] hover:bg-[var(--action-secondary-hover)] active:bg-[var(--bg-card-hover)] text-[var(--text-primary)] border border-[var(--border-default)] shadow-xs active:translate-y-[0.5px]",
  tertiary:
    "bg-transparent hover:bg-[var(--bg-secondary)] active:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-transparent active:translate-y-[0.5px]",
  ghost:
    "bg-transparent hover:bg-[var(--bg-card-hover)] active:bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-transparent active:translate-y-[0.5px]",
  danger:
    "bg-[var(--color-danger)] hover:opacity-90 active:opacity-95 text-white border border-transparent shadow-xs active:translate-y-[0.5px]",
  destructive:
    "bg-[var(--color-danger)] hover:opacity-90 active:opacity-95 text-white border border-transparent shadow-xs active:translate-y-[0.5px]",
  outline:
    "bg-transparent hover:bg-[var(--bg-card-hover)] active:bg-[var(--bg-secondary)] text-[var(--text-primary)] border border-[var(--border-default)] hover:border-[var(--border-strong)] active:translate-y-[0.5px]",
};

const sizeClasses: Record<ButtonSize, string> = {
  xs: "text-xs px-2.5 py-1 rounded gap-1.5 h-7",
  sm: "text-xs px-3 py-1.5 rounded-md gap-1.5 h-8",
  md: "text-sm px-4 py-2 rounded-md gap-2 h-9",
  lg: "text-base px-5 py-2.5 rounded-lg gap-2.5 h-11",
  icon: "p-1.5 rounded-md w-8 h-8 items-center justify-center",
};

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  iconOnly?: boolean;
  "aria-label"?: string;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  leftIcon,
  rightIcon,
  iconOnly = false,
  className,
  disabled,
  "aria-label": ariaLabel,
  ...props
}: ButtonProps) {
  const resolvedSize: ButtonSize = iconOnly ? "icon" : size;

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium transition-all duration-150 select-none",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--bg-base)]",
        "disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none",
        variantClasses[variant],
        sizeClasses[resolvedSize],
        className
      )}
      disabled={disabled || loading}
      aria-busy={loading}
      aria-disabled={disabled || loading}
      aria-label={ariaLabel}
      {...props}
    >
      {loading ? (
        <SpinnerIcon size="sm" className="text-current" />
      ) : (
        leftIcon && <span className="inline-flex items-center flex-shrink-0" aria-hidden="true">{leftIcon}</span>
      )}
      {children}
      {!loading && rightIcon && (
        <span className="inline-flex items-center flex-shrink-0" aria-hidden="true">{rightIcon}</span>
      )}
    </button>
  );
}

export default Button;
