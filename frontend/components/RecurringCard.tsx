import React from "react";
import { format, parseISO } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import {
  Calendar,
  DollarSign,
  TrendingUp,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { formatCurrency } from "@/utils/currency";

interface RecurringPattern {
  id?: number;
  merchant: string;
  category?: string;
  average_amount: number;
  amount_variance: number;
  frequency: string;
  next_expected?: string;
  confidence: number;
  occurrences: string[];
  should_skip_dates: string[];
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

interface RecurringCardProps {
  pattern: RecurringPattern;
}

const RecurringCard: React.FC<RecurringCardProps> = ({ pattern }) => {
  const getFrequencyLabel = (frequency: string) => {
    const labels: Record<string, string> = {
      weekly: "Weekly",
      biweekly: "Every 2 weeks",
      monthly: "Monthly",
      quarterly: "Quarterly",
      annual: "Annually",
    };
    return labels[frequency.toLowerCase()] || frequency;
  };

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 90) return "✓✓";
    if (confidence >= 70) return "✓";
    return "?";
  };

  const recentOccurrences = pattern.occurrences
    .slice(-5)
    .reverse()
    .map((d) => parseISO(d));

  const lastOccurrence = pattern.occurrences.length > 0
    ? parseISO(pattern.occurrences[pattern.occurrences.length - 1])
    : null;

  return (
    <div className="space-y-6">
      {/* Confidence Score */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Confidence Score
            </p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
              {pattern.confidence}%
            </p>
          </div>
          <div className="text-4xl">
            {getConfidenceIcon(pattern.confidence)}
          </div>
        </div>
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-2">
          Based on {pattern.occurrences.length} detected occurrences
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-3">
        <Card>
          <CardContent className="p-3">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
              <DollarSign className="w-4 h-4" />
              <span className="text-xs">Average Amount</span>
            </div>
            <p className="text-lg font-semibold text-slate-900 dark:text-white mt-1">
              {formatCurrency(pattern.average_amount, "CAD")}
            </p>
            {pattern.amount_variance > 0 && (
              <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
                ±{pattern.amount_variance.toFixed(2)}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-3">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
              <TrendingUp className="w-4 h-4" />
              <span className="text-xs">Frequency</span>
            </div>
            <p className="text-lg font-semibold text-slate-900 dark:text-white mt-1">
              {getFrequencyLabel(pattern.frequency)}
            </p>
          </CardContent>
        </Card>

        {pattern.next_expected && (
          <Card className="col-span-2">
            <CardContent className="p-3">
              <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                <Calendar className="w-4 h-4" />
                <span className="text-xs">Next Expected</span>
              </div>
              <p className="text-lg font-semibold text-slate-900 dark:text-white mt-1">
                {format(parseISO(pattern.next_expected), "EEEE, MMMM d, yyyy")}
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Recent Occurrences Timeline */}
      <div>
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
          Recent Occurrences
        </h4>
        {recentOccurrences.length > 0 ? (
          <div className="space-y-2">
            {recentOccurrences.map((date, index) => {
              const isSkipped = pattern.should_skip_dates.some(
                (d) =>
                  format(parseISO(d), "yyyy-MM-dd") ===
                  format(date, "yyyy-MM-dd")
              );
              return (
                <div
                  key={index}
                  className={cn(
                    "flex items-center justify-between p-2 rounded border",
                    isSkipped
                      ? "bg-orange-50 dark:bg-orange-950 border-orange-200 dark:border-orange-800"
                      : "bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700"
                  )}
                >
                  <span className="text-sm">
                    {format(date, "MMM d, yyyy")} (
                    {format(date, "EEEE")})
                  </span>
                  {isSkipped && (
                    <Badge variant="warning" size="sm">
                      Skipped
                    </Badge>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-slate-500 dark:text-slate-500">
            No occurrences recorded yet
          </p>
        )}
      </div>

      {/* Details */}
      <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
        <div className="text-xs text-slate-600 dark:text-slate-400 space-y-2">
          {pattern.category && (
            <div>
              <span className="font-medium">Category:</span> {pattern.category}
            </div>
          )}
          {pattern.created_at && (
            <div>
              <span className="font-medium">Created:</span>{" "}
              {format(parseISO(pattern.created_at), "MMM d, yyyy")}
            </div>
          )}
          {pattern.updated_at && (
            <div>
              <span className="font-medium">Last Updated:</span>{" "}
              {format(parseISO(pattern.updated_at), "MMM d, yyyy")}
            </div>
          )}
        </div>
      </div>

      {/* Known Skips Warning */}
      {pattern.should_skip_dates.length > 0 && (
        <div className="bg-amber-50 dark:bg-amber-950 rounded-lg p-3 border border-amber-200 dark:border-amber-800">
          <div className="flex gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-amber-900 dark:text-amber-200">
                Known Delays
              </p>
              <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                {pattern.should_skip_dates.length} expected date
                {pattern.should_skip_dates.length !== 1 ? "s" : ""} without
                transactions
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecurringCard;
