/**
 * components/ui/Input.tsx
 * =======================
 * Institutional form input system for Seance:
 * - Input (text, number, email, search)
 * - Textarea
 * - Select
 * - Checkbox
 *
 * Implements:
 * - Clear focus ring with `--focus-ring`
 * - Error and validation states with `--color-danger`
 * - Readable placeholder and label typography
 * - Disabled and readonly states
 */

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";
import { ChevronDownIcon, CheckIcon } from "./Icons";

// ---------------------------------------------------------------------------
// Text Input
// ---------------------------------------------------------------------------

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      helperText,
      error,
      leftIcon,
      rightIcon,
      id,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    const inputId = id || (label ? `input-${label.toLowerCase().replace(/\s+/g, "-")}` : undefined);

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-semibold text-[var(--text-secondary)]"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center w-full">
          {leftIcon && (
            <span
              className="absolute left-3 text-[var(--text-muted)] pointer-events-none inline-flex items-center"
              aria-hidden="true"
            >
              {leftIcon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            aria-invalid={!!error}
            aria-describedby={
              error
                ? `${inputId}-error`
                : helperText
                ? `${inputId}-helper`
                : undefined
            }
            className={cn(
              "w-full rounded-lg border bg-[var(--input-bg)] px-3.5 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] transition-all duration-150",
              "focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring)] focus:border-transparent",
              "disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-[var(--disabled-bg)]",
              leftIcon && "pl-9",
              rightIcon && "pr-9",
              error
                ? "border-[var(--color-danger)] focus:ring-[var(--color-danger)]"
                : "border-[var(--input-border)] hover:border-[var(--border-strong)]",
              className
            )}
            {...props}
          />
          {rightIcon && (
            <span
              className="absolute right-3 text-[var(--text-muted)] pointer-events-none inline-flex items-center"
              aria-hidden="true"
            >
              {rightIcon}
            </span>
          )}
        </div>
        {error ? (
          <p id={`${inputId}-error`} className="text-xs text-[var(--color-danger)] font-medium" role="alert">
            {error}
          </p>
        ) : helperText ? (
          <p id={`${inputId}-helper`} className="text-xs text-[var(--text-muted)]">
            {helperText}
          </p>
        ) : null}
      </div>
    );
  }
);
Input.displayName = "Input";

// ---------------------------------------------------------------------------
// Textarea
// ---------------------------------------------------------------------------

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  helperText?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, helperText, error, id, className, disabled, rows = 3, ...props }, ref) => {
    const inputId = id || (label ? `textarea-${label.toLowerCase().replace(/\s+/g, "-")}` : undefined);

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-semibold text-[var(--text-secondary)]"
          >
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          rows={rows}
          disabled={disabled}
          aria-invalid={!!error}
          className={cn(
            "w-full rounded-lg border bg-[var(--input-bg)] px-3.5 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] transition-all duration-150 resize-y",
            "focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring)] focus:border-transparent",
            "disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-[var(--disabled-bg)]",
            error
              ? "border-[var(--color-danger)] focus:ring-[var(--color-danger)]"
              : "border-[var(--input-border)] hover:border-[var(--border-strong)]",
            className
          )}
          {...props}
        />
        {error ? (
          <p className="text-xs text-[var(--color-danger)] font-medium" role="alert">
            {error}
          </p>
        ) : helperText ? (
          <p className="text-xs text-[var(--text-muted)]">{helperText}</p>
        ) : null}
      </div>
    );
  }
);
Textarea.displayName = "Textarea";

// ---------------------------------------------------------------------------
// Select
// ---------------------------------------------------------------------------

export interface SelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  helperText?: string;
  error?: string;
  options?: Array<{ value: string; label: string; disabled?: boolean }>;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      label,
      helperText,
      error,
      id,
      className,
      disabled,
      options,
      children,
      ...props
    },
    ref
  ) => {
    const inputId = id || (label ? `select-${label.toLowerCase().replace(/\s+/g, "-")}` : undefined);

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-semibold text-[var(--text-secondary)]"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center w-full">
          <select
            ref={ref}
            id={inputId}
            disabled={disabled}
            className={cn(
              "w-full appearance-none rounded-lg border bg-[var(--input-bg)] px-3.5 py-2 pr-9 text-sm text-[var(--text-primary)] transition-all duration-150 cursor-pointer",
              "focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring)] focus:border-transparent",
              "disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-[var(--disabled-bg)]",
              error
                ? "border-[var(--color-danger)] focus:ring-[var(--color-danger)]"
                : "border-[var(--input-border)] hover:border-[var(--border-strong)]",
              className
            )}
            {...props}
          >
            {options
              ? options.map((opt) => (
                  <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                    {opt.label}
                  </option>
                ))
              : children}
          </select>
          <span
            className="absolute right-3 text-[var(--text-muted)] pointer-events-none inline-flex items-center"
            aria-hidden="true"
          >
            <ChevronDownIcon size="xs" />
          </span>
        </div>
        {error ? (
          <p className="text-xs text-[var(--color-danger)] font-medium" role="alert">
            {error}
          </p>
        ) : helperText ? (
          <p className="text-xs text-[var(--text-muted)]">{helperText}</p>
        ) : null}
      </div>
    );
  }
);
Select.displayName = "Select";

// ---------------------------------------------------------------------------
// Checkbox
// ---------------------------------------------------------------------------

export interface CheckboxProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
  description?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, description, id, className, disabled, checked, ...props }, ref) => {
    const inputId = id || (label ? `chk-${label.toLowerCase().replace(/\s+/g, "-")}` : undefined);

    return (
      <label
        htmlFor={inputId}
        className={cn(
          "inline-flex items-start gap-2.5 cursor-pointer select-none",
          disabled && "cursor-not-allowed opacity-50",
          className
        )}
      >
        <div className="relative flex items-center justify-center mt-0.5">
          <input
            ref={ref}
            type="checkbox"
            id={inputId}
            disabled={disabled}
            checked={checked}
            className="peer sr-only"
            {...props}
          />
          <div
            className={cn(
              "w-4 h-4 rounded border transition-all duration-150 flex items-center justify-center",
              "border-[var(--input-border)] bg-[var(--input-bg)]",
              "peer-focus-visible:ring-2 peer-focus-visible:ring-[var(--focus-ring)] peer-focus-visible:ring-offset-1 peer-focus-visible:ring-offset-[var(--bg-base)]",
              "peer-checked:bg-[var(--action-primary)] peer-checked:border-[var(--action-primary)] text-[var(--text-primary)]"
            )}
          >
            <CheckIcon size="xs" className="opacity-0 peer-checked:opacity-100 transition-opacity stroke-[2.5]" />
          </div>
        </div>
        {(label || description) && (
          <div className="text-xs">
            {label && (
              <span className="font-medium text-[var(--text-primary)] block">
                {label}
              </span>
            )}
            {description && (
              <span className="text-[var(--text-muted)] block mt-0.5">
                {description}
              </span>
            )}
          </div>
        )}
      </label>
    );
  }
);
Checkbox.displayName = "Checkbox";
