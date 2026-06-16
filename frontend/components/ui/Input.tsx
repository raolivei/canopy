import React, { forwardRef } from "react";
import { cn } from "@/utils/cn";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  inputSize?: "sm" | "md" | "lg";
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      inputSize = "md",
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || label?.toLowerCase().replace(/\s/g, "-");

    const sizes = {
      sm: "sm:px-3 sm:py-1.5 px-3 py-1 text-xs sm:text-sm",
      md: "sm:px-3 sm:py-2 px-3 py-1.5 text-sm sm:text-base",
      lg: "sm:px-4 sm:py-3 px-4 py-2 text-base sm:text-lg",
    };

    const baseInputStyles = cn(
      "w-full bg-white dark:bg-slate-900",
      "border border-slate-300 dark:border-slate-700 rounded-md",
      "text-slate-900 dark:text-slate-100",
      "placeholder:text-slate-400 dark:placeholder:text-slate-500",
      "transition-colors duration-150",
      "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
      "disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-slate-100 dark:disabled:bg-slate-800",
      error && "border-danger-500 focus:ring-danger-500 focus:border-danger-500",
      leftIcon && "pl-10",
      rightIcon && "pr-10",
      sizes[inputSize]
    );

    return (
      <div className={cn("w-full", className)}>
        {label && (
          <label
            htmlFor={inputId}
            className="block sm:text-sm text-xs font-medium text-slate-700 dark:text-slate-300 mb-1 sm:mb-1.5"
          >
            {label}
            {props.required && <span aria-label="required" className="text-danger-600 ml-1">*</span>}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" aria-hidden="true">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={baseInputStyles}
            aria-invalid={!!error}
            aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" aria-hidden="true">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p id={`${inputId}-error`} className="text-xs text-danger-600 dark:text-danger-400 mt-1" role="alert">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={`${inputId}-helper`} className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, helperText, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s/g, "-");

    return (
      <div className={cn("w-full", className)}>
        {label && (
          <label
            htmlFor={inputId}
            className="block sm:text-sm text-xs font-medium text-slate-700 dark:text-slate-300 mb-1 sm:mb-1.5"
          >
            {label}
            {props.required && <span aria-label="required" className="text-danger-600 ml-1">*</span>}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={cn(
            "w-full sm:px-3 sm:py-2 px-3 py-1.5 sm:text-sm text-xs",
            "bg-white dark:bg-slate-900",
            "border border-slate-300 dark:border-slate-700 rounded-md",
            "text-slate-900 dark:text-slate-100",
            "placeholder:text-slate-400 dark:placeholder:text-slate-500",
            "transition-colors duration-150 resize-none",
            "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            error && "border-danger-500 focus:ring-danger-500 focus:border-danger-500"
          )}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} className="text-xs text-danger-600 dark:text-danger-400 mt-1" role="alert">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={`${inputId}-helper`} className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = "Textarea";

export { Input, Textarea };
