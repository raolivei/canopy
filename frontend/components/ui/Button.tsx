import React, { forwardRef, useEffect, useState } from "react";
import { Loader2, CheckCircle2 } from "lucide-react";
import { cn } from "@/utils/cn";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "success";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  loadingText?: string;
  successText?: string;
  showSuccess?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      loading = false,
      loadingText,
      successText = "Done ✓",
      showSuccess = false,
      leftIcon,
      rightIcon,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const [isShowingSuccess, setIsShowingSuccess] = useState(false);

    // Auto-dismiss success state after 1s
    useEffect(() => {
      if (showSuccess && !isShowingSuccess) {
        setIsShowingSuccess(true);
        const timer = setTimeout(() => {
          setIsShowingSuccess(false);
        }, 1000);
        return () => clearTimeout(timer);
      }
    }, [showSuccess, isShowingSuccess]);
    const baseStyles =
      "inline-flex items-center justify-center gap-2 font-medium rounded-md transition-all duration-150 ease-smooth focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]";

    const variants = {
      primary:
        "bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500 shadow-sm hover:shadow",
      secondary:
        "bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 hover:border-slate-400 dark:hover:border-slate-600 focus-visible:ring-slate-500",
      ghost:
        "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100 focus-visible:ring-slate-500",
      danger:
        "bg-danger-600 text-white hover:bg-danger-700 focus-visible:ring-danger-500",
      success:
        "bg-success-600 text-white hover:bg-success-700 focus-visible:ring-success-500",
    };

    const sizes = {
      sm: "px-3 py-1.5 text-sm",
      md: "px-4 py-2 text-sm",
      lg: "px-6 py-3 text-base",
    };

    const displayText = isShowingSuccess
      ? successText
      : loading && loadingText
      ? loadingText
      : children;

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || loading}
        {...props}
      >
        {isShowingSuccess ? (
          <CheckCircle2 className="w-4 h-4" />
        ) : loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          leftIcon && <span className="shrink-0">{leftIcon}</span>
        )}
        <span className="transition-opacity duration-200">{displayText}</span>
        {!loading && !isShowingSuccess && rightIcon && (
          <span className="shrink-0">{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button };
