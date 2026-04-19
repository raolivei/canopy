import React from "react";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular" | "card";
  width?: string | number;
  height?: string | number;
  count?: number;
}

export default function SkeletonLoader({
  className = "",
  variant = "text",
  width,
  height,
  count = 1,
}: SkeletonProps) {
  const baseClasses =
    "animate-pulse bg-slate-200 dark:bg-slate-700 rounded";

  const variantClasses = {
    text: "h-4",
    circular: "rounded-full",
    rectangular: "",
    card: "h-32 rounded-card",
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === "number" ? `${width}px` : width;
  if (height) style.height = typeof height === "number" ? `${height}px` : height;

  if (count > 1) {
    return (
      <>
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className={`${baseClasses} ${variantClasses[variant]} ${className}`}
            style={i === 0 ? style : undefined}
          />
        ))}
      </>
    );
  }

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
    />
  );
}

export function StatCardSkeleton() {
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <SkeletonLoader
          variant="rectangular"
          width={48}
          height={48}
          className="rounded-xl"
        />
        <SkeletonLoader
          variant="rectangular"
          width={80}
          height={24}
          className="rounded-lg"
        />
      </div>
      <SkeletonLoader variant="text" width="40%" className="mb-2" />
      <SkeletonLoader variant="text" width="60%" height={32} />
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <SkeletonLoader
            variant="text"
            width={120}
            height={24}
            className="mb-2"
          />
          <SkeletonLoader variant="text" width={80} height={16} />
        </div>
        <SkeletonLoader
          variant="rectangular"
          width={200}
          height={32}
          className="rounded-lg"
        />
      </div>
      <SkeletonLoader variant="card" height={300} />
    </div>
  );
}

export function TransactionSkeleton() {
  return (
    <div className="divide-y divide-slate-100 dark:divide-slate-700">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <SkeletonLoader variant="circular" width={48} height={48} />
              <div>
                <SkeletonLoader
                  variant="text"
                  width={150}
                  height={20}
                  className="mb-2"
                />
                <SkeletonLoader variant="text" width={100} height={16} />
              </div>
            </div>
            <div className="text-right">
              <SkeletonLoader
                variant="text"
                width={80}
                height={20}
                className="mb-1"
              />
              <SkeletonLoader variant="text" width={60} height={14} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
