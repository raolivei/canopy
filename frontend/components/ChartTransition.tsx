import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SkeletonChart } from "@/components/ui/Skeleton";

/**
 * ChartTransition
 *
 * Wraps chart components with smooth skeleton→data animations.
 * Shows skeleton placeholder while `isLoading` is true,
 * then animates in the actual chart content with fade + slide.
 */
export function ChartTransition({
  children,
  isLoading,
}: {
  children: React.ReactNode;
  isLoading: boolean;
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
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
