import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SkeletonChart } from "@/components/ui/Skeleton";
import { cn } from "@/utils/cn";

/**
 * ChartTransition
 *
 * Wraps chart components with smooth skeleton→data animations.
 * Shows skeleton placeholder while `isLoading` is true,
 * then animates in the actual chart content with fade + slide.
 *
 * @param children - The chart component to render
 * @param isLoading - Whether to show skeleton (true) or content (false)
 * @param skeletonClassName - Optional CSS classes for skeleton container
 * @param contentClassName - Optional CSS classes for content wrapper
 */
export function ChartTransition({
  children,
  isLoading,
  skeletonClassName,
  contentClassName,
}: {
  children: React.ReactNode;
  isLoading: boolean;
  skeletonClassName?: string;
  contentClassName?: string;
}) {
  return (
    <AnimatePresence mode="wait">
      {isLoading ? (
        <motion.div
          key="skeleton"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className={cn("w-full", skeletonClassName)}
        >
          <SkeletonChart />
        </motion.div>
      ) : (
        <motion.div
          key="content"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className={cn("w-full", contentClassName)}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
