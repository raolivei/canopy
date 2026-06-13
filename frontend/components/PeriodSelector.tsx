import React, { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Calendar } from "lucide-react";
import { cn } from "@/utils/cn";

export type BudgetPeriod = "MONTHLY" | "QUARTERLY" | "ANNUAL";

interface DateRange {
  start: string;
  end: string;
}

interface PeriodSelectorProps {
  selectedPeriod: BudgetPeriod;
  onPeriodChange: (period: BudgetPeriod) => void;
  showCustomRange?: boolean;
  onCustomRangeChange?: (range: DateRange) => void;
  compact?: boolean;
}

const periodConfig = {
  MONTHLY: { label: "Monthly", badge: "M" },
  QUARTERLY: { label: "Quarterly", badge: "Q" },
  ANNUAL: { label: "Annually", badge: "Y" },
};

export default function PeriodSelector({
  selectedPeriod,
  onPeriodChange,
  showCustomRange = false,
  onCustomRangeChange,
  compact = false,
}: PeriodSelectorProps) {
  const [isCustomModalOpen, setIsCustomModalOpen] = useState(false);
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");

  const handleCustomRangeConfirm = () => {
    if (customStart && customEnd && onCustomRangeChange) {
      onCustomRangeChange({ start: customStart, end: customEnd });
      setIsCustomModalOpen(false);
      setCustomStart("");
      setCustomEnd("");
    }
  };

  const periods: BudgetPeriod[] = ["MONTHLY", "QUARTERLY", "ANNUAL"];

  return (
    <>
      <div className={cn("flex items-center gap-2", compact && "gap-1")}>
        {periods.map((period) => (
          <Button
            key={period}
            variant={selectedPeriod === period ? "primary" : "secondary"}
            size={compact ? "sm" : "md"}
            onClick={() => onPeriodChange(period)}
            className={compact ? "px-3 py-1 text-xs" : ""}
          >
            {compact ? periodConfig[period].badge : periodConfig[period].label}
          </Button>
        ))}

        {showCustomRange && (
          <Button
            variant={selectedPeriod === "CUSTOM" ? "primary" : "secondary"}
            size={compact ? "sm" : "md"}
            onClick={() => setIsCustomModalOpen(true)}
            leftIcon={<Calendar className={cn("w-4 h-4", compact && "w-3 h-3")} />}
            className={compact ? "px-3 py-1 text-xs" : ""}
          >
            {compact ? "Custom" : "Custom Range"}
          </Button>
        )}
      </div>

      <Modal
        isOpen={isCustomModalOpen}
        onClose={() => setIsCustomModalOpen(false)}
        title="Custom Date Range"
        description="Select a custom date range for your budget"
        size="sm"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setIsCustomModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleCustomRangeConfirm}
              disabled={!customStart || !customEnd}
            >
              Apply
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Start Date"
            type="date"
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
          />
          <Input
            label="End Date"
            type="date"
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
            error={
              customStart && customEnd && new Date(customEnd) < new Date(customStart)
                ? "End date must be after start date"
                : undefined
            }
          />
        </div>
      </Modal>
    </>
  );
}
