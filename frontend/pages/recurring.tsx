import React, { useState, useMemo } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { SkeletonList, RecurringStatsSkeleton, RecurringCardSkeleton } from "@/components/ui/Skeleton";
import RecurringList, { RecurringPattern } from "@/components/RecurringList";
import {
  RefreshCw,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Zap,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { motion } from "framer-motion";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

interface DetectionResponse {
  detected: RecurringPattern[];
  total_count: number;
}

interface ApiError {
  detail?: string;
}

export default function RecurringPage() {
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false);
  const [detectedPatterns, setDetectedPatterns] = useState<RecurringPattern[]>([]);

  const {
    data: storedPatterns = [],
    isLoading: isLoadingStored,
    refetch: refetchStored,
  } = useQuery<RecurringPattern[]>({
    queryKey: ["recurring-patterns"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/recurring/`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to fetch patterns");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });

  const { mutate: detectPatterns, isPending: isDetecting } = useMutation({
    mutationFn: async (lookbackMonths: number = 12) => {
      const res = await fetch(
        `${API_URL}/v1/recurring/detect?lookback_months=${lookbackMonths}`,
        { credentials: "include" }
      );
      if (!res.ok) {
        const error = (await res.json()) as ApiError;
        throw new Error(error.detail || "Detection failed");
      }
      return res.json() as Promise<DetectionResponse>;
    },
    onSuccess: (data) => {
      setDetectedPatterns(data.detected);
      setIsApprovalModalOpen(true);
      showToast(`Found ${data.total_count} recurring patterns`);
    },
    onError: (error: Error) => {
      showToast(`Error: ${error.message}`, "error");
    },
  });

  const { mutate: createPattern } = useMutation({
    mutationFn: async (pattern: RecurringPattern) => {
      const res = await fetch(`${API_URL}/v1/recurring/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(pattern),
      });
      if (!res.ok) throw new Error("Failed to save pattern");
      return res.json() as Promise<RecurringPattern>;
    },
    onSuccess: () => {
      refetchStored();
    },
    onError: (error: Error) => {
      showToast(`Error: ${error.message}`, "error");
    },
  });

  const { mutate: updatePattern } = useMutation({
    mutationFn: async (pattern: RecurringPattern) => {
      if (!pattern.id) throw new Error("Pattern ID required");
      const res = await fetch(`${API_URL}/v1/recurring/${pattern.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          frequency: pattern.frequency,
          average_amount: pattern.average_amount,
          next_expected: pattern.next_expected,
          is_active: pattern.is_active,
        }),
      });
      if (!res.ok) throw new Error("Failed to update pattern");
      return res.json() as Promise<RecurringPattern>;
    },
    onSuccess: () => {
      refetchStored();
    },
    onError: (error: Error) => {
      showToast(`Error: ${error.message}`, "error");
    },
  });

  const { mutate: deletePattern } = useMutation({
    mutationFn: async (patternId: number) => {
      const res = await fetch(`${API_URL}/v1/recurring/${patternId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to delete pattern");
      return res.json();
    },
    onSuccess: () => {
      refetchStored();
      showToast("Pattern deleted");
    },
    onError: (error: Error) => {
      showToast(`Error: ${error.message}`, "error");
    },
  });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleApproveSingle = (pattern: RecurringPattern) => {
    createPattern(pattern);
    setDetectedPatterns(
      detectedPatterns.filter((p) => p.merchant !== pattern.merchant)
    );
  };

  const handleDismiss = (pattern: RecurringPattern) => {
    setDetectedPatterns(
      detectedPatterns.filter((p) => p.merchant !== pattern.merchant)
    );
  };

  const stats = useMemo(
    () => ({
      total: storedPatterns.length,
      active: storedPatterns.filter((p) => p.is_active).length,
      avgConfidence:
        storedPatterns.length > 0
          ? Math.round(
              storedPatterns.reduce((sum, p) => sum + p.confidence, 0) /
                storedPatterns.length
            )
          : 0,
    }),
    [storedPatterns]
  );

  return (
    <PageLayout>
      <PageHeader
        title="Recurring Transactions"
        description="Manage and predict recurring expenses and income"
        icon={<TrendingUp className="w-8 h-8" />}
      />

      {toastMessage && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed top-4 right-4 z-50 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 px-4 py-3 rounded-lg shadow-lg"
        >
          {toastMessage}
        </motion.div>
      )}

      {isLoadingStored ? (
        <RecurringStatsSkeleton />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Total Patterns
                  </p>
                  <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                    {stats.total}
                  </p>
                </div>
                <CheckCircle className="w-8 h-8 text-slate-400" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Active Now
                  </p>
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">
                    {stats.active}
                  </p>
                </div>
                <Zap className="w-8 h-8 text-green-400" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Avg Confidence
                  </p>
                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                    {stats.avgConfidence}%
                  </p>
                </div>
                <Badge variant="primary">
                  {stats.avgConfidence > 85 ? "High" : "Good"}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Card className="mb-6 border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950">
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-lg">Detection Tool</CardTitle>
          <Button
            onClick={() => detectPatterns(12)}
            disabled={isDetecting}
            className="flex items-center gap-2"
          >
            <RefreshCw
              className={cn("w-4 h-4", isDetecting && "animate-spin")}
            />
            {isDetecting ? "Detecting..." : "Detect Patterns"}
          </Button>
        </CardHeader>
        <CardContent className="text-sm text-slate-700 dark:text-slate-300">
          <p>
            Click to analyze your last 12 months of transactions for recurring
            patterns. Patterns with 70%+ confidence will be suggested.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Your Patterns</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoadingStored ? (
            <SkeletonList />
          ) : (
            <RecurringList
              patterns={storedPatterns}
              onUpdate={updatePattern}
              onDelete={deletePattern}
              loading={false}
            />
          )}
        </CardContent>
      </Card>

      <Modal
        isOpen={isApprovalModalOpen}
        onClose={() => setIsApprovalModalOpen(false)}
        title={`Review ${detectedPatterns.length} Detected Patterns`}
      >
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {detectedPatterns.length === 0 ? (
            <div className="py-8 text-center text-slate-500">
              <AlertCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No patterns to review</p>
            </div>
          ) : (
            <>
              {detectedPatterns.map((pattern, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="border border-slate-200 dark:border-slate-700 rounded-lg p-4"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-semibold text-slate-900 dark:text-white">
                        {pattern.merchant}
                      </h4>
                      {pattern.category && (
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          {pattern.category}
                        </p>
                      )}
                    </div>
                    <Badge
                      variant={
                        pattern.confidence >= 90
                          ? "success"
                          : pattern.confidence >= 70
                            ? "warning"
                            : "danger"
                      }
                    >
                      {pattern.confidence}%
                    </Badge>
                  </div>
                  <div className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                    <p>
                      ${pattern.average_amount.toFixed(2)} •{" "}
                      {pattern.frequency} • {pattern.occurrences.length} times
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => handleApproveSingle(pattern)}
                      className="flex-1"
                    >
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => handleDismiss(pattern)}
                      className="flex-1"
                    >
                      Skip
                    </Button>
                  </div>
                </motion.div>
              ))}

              <div className="flex gap-3 pt-4 border-t border-slate-200 dark:border-slate-700">
                <Button
                  onClick={() => {
                    detectedPatterns.forEach((pattern) => {
                      createPattern(pattern);
                    });
                    setIsApprovalModalOpen(false);
                    setDetectedPatterns([]);
                  }}
                  className="flex-1"
                >
                  Approve All
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setIsApprovalModalOpen(false);
                    setDetectedPatterns([]);
                  }}
                  className="flex-1"
                >
                  Close
                </Button>
              </div>
            </>
          )}
        </div>
      </Modal>
    </PageLayout>
  );
}
