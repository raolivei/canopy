import React from "react";
import { motion } from "framer-motion";
import { AnimatePresence } from "framer-motion";

interface ChartTransitionProps {
  isLoading: boolean;
  skeleton: React.ReactNode;
  chart: React.ReactNode;
  layoutId?: string;
}

/**
 * Wrapper for smooth skeleton→chart transitions
 * Shows skeleton, then animates to chart with cross-fade
 */
export default function ChartTransition({
  isLoading,
  skeleton,
  chart,
  layoutId,
}: ChartTransitionProps) {
  return (
    <AnimatePresence mode="wait">
      {isLoading ? (
        <motion.div
          key="skeleton"
          layoutId={layoutId ? `${layoutId}-skeleton` : undefined}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          {skeleton}
        </motion.div>
      ) : (
        <motion.div
          key="chart"
          layoutId={layoutId ? `${layoutId}-chart` : undefined}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {chart}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/**
 * Tween a number value with animation
 */
export function AnimatedNumber({
  value,
  formatter = (v) => v.toString(),
}: {
  value: number;
  formatter?: (v: number) => string;
}) {
  const [displayValue, setDisplayValue] = React.useState(value);

  React.useEffect(() => {
    const startValue = displayValue;
    const duration = 600; // ms
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);

      const current = startValue + (value - startValue) * progress;
      setDisplayValue(Math.round(current * 100) / 100);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    animate();
  }, [value, displayValue]);

  return <>{formatter(displayValue)}</>;
}
