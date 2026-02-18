import React, { useState, useEffect, useCallback, createContext, useContext } from "react";
import { createPortal } from "react-dom";
import { X, CheckCircle2, AlertCircle, AlertTriangle, Info } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/utils/cn";

type ToastVariant = "success" | "danger" | "warning" | "info";

export interface ToastData {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
}

interface ToastContextValue {
  toasts: ToastData[];
  addToast: (toast: Omit<ToastData, "id">) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

let toastCounter = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const addToast = useCallback((toast: Omit<ToastData, "id">) => {
    const id = `toast-${++toastCounter}-${Date.now()}`;
    setToasts((prev) => [...prev, { ...toast, id }]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

const variantConfig: Record<
  ToastVariant,
  {
    icon: React.ElementType;
    containerClass: string;
    iconClass: string;
  }
> = {
  success: {
    icon: CheckCircle2,
    containerClass:
      "border-success-200 dark:border-success-800 bg-white dark:bg-slate-900",
    iconClass: "text-success-500",
  },
  danger: {
    icon: AlertCircle,
    containerClass:
      "border-danger-200 dark:border-danger-800 bg-white dark:bg-slate-900",
    iconClass: "text-danger-500",
  },
  warning: {
    icon: AlertTriangle,
    containerClass:
      "border-warning-200 dark:border-warning-800 bg-white dark:bg-slate-900",
    iconClass: "text-warning-500",
  },
  info: {
    icon: Info,
    containerClass:
      "border-primary-200 dark:border-primary-800 bg-white dark:bg-slate-900",
    iconClass: "text-primary-500",
  },
};

function ToastItem({
  toast,
  onRemove,
}: {
  toast: ToastData;
  onRemove: (id: string) => void;
}) {
  const duration = toast.duration ?? 5000;
  const variant = toast.variant ?? "info";
  const config = variantConfig[variant];
  const Icon = config.icon;

  useEffect(() => {
    if (duration <= 0) return;
    const timer = setTimeout(() => onRemove(toast.id), duration);
    return () => clearTimeout(timer);
  }, [toast.id, duration, onRemove]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -10, scale: 0.95, transition: { duration: 0.15 } }}
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      className={cn(
        "pointer-events-auto w-full max-w-sm rounded-lg border shadow-lg",
        "flex items-start gap-3 p-4",
        config.containerClass
      )}
    >
      <Icon className={cn("w-5 h-5 shrink-0 mt-0.5", config.iconClass)} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-900 dark:text-white">
          {toast.title}
        </p>
        {toast.description && (
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {toast.description}
          </p>
        )}
      </div>
      <button
        onClick={() => onRemove(toast.id)}
        className="shrink-0 p-1 -mr-1 -mt-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </motion.div>
  );
}

function ToastContainer({
  toasts,
  onRemove,
}: {
  toasts: ToastData[];
  onRemove: (id: string) => void;
}) {
  if (typeof window === "undefined") return null;

  return createPortal(
    <div className="fixed bottom-4 right-4 z-[60] flex flex-col-reverse gap-2 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
        ))}
      </AnimatePresence>
    </div>,
    document.body
  );
}

export { ToastContainer };
