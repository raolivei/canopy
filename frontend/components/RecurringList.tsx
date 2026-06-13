import React, { useState } from "react";
import { format, parseISO } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal, ConfirmModal } from "@/components/ui/Modal";
import {
  Edit2,
  Trash2,
  Calendar,
  DollarSign,
  AlertCircle,
  CheckCircle,
  Eye,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { formatCurrency } from "@/utils/currency";
import { motion } from "framer-motion";
import RecurringForm from "./RecurringForm";
import RecurringCard from "./RecurringCard";

export interface RecurringPattern {
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

interface RecurringListProps {
  patterns: RecurringPattern[];
  loading?: boolean;
  onApprove?: (pattern: RecurringPattern) => void;
  onUpdate?: (pattern: RecurringPattern) => void;
  onDismiss?: (patternId: number) => void;
  onDelete?: (patternId: number) => void;
}

const RecurringList: React.FC<RecurringListProps> = ({
  patterns,
  loading = false,
  onApprove,
  onUpdate,
  onDismiss,
  onDelete,
}) => {
  const [selectedPattern, setSelectedPattern] = useState<RecurringPattern | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const getConfidenceBadgeVariant = (confidence: number) => {
    if (confidence >= 90) return "success";
    if (confidence >= 70) return "warning";
    return "danger";
  };

  const getFrequencyLabel = (frequency: string) => {
    const labels: Record<string, string> = {
      weekly: "Weekly",
      biweekly: "Biweekly",
      monthly: "Monthly",
      quarterly: "Quarterly",
      annual: "Annual",
    };
    return labels[frequency.toLowerCase()] || frequency;
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="h-16 bg-slate-200 dark:bg-slate-700" />
          </Card>
        ))}
      </div>
    );
  }

  if (patterns.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-12 text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-slate-400" />
          <p className="text-slate-600 dark:text-slate-400">
            No recurring patterns detected yet.
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-500 mt-2">
            Patterns will appear after analyzing your transaction history.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Active patterns */}
      {patterns.filter((p) => p.is_active).length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
            Active Patterns ({patterns.filter((p) => p.is_active).length})
          </h3>
          <div className="space-y-3">
            {patterns
              .filter((p) => p.is_active)
              .map((pattern, index) => (
                <motion.div
                  key={pattern.id || index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-4">
                        {/* Left: Pattern info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-2">
                            <div>
                              <h4 className="font-semibold text-slate-900 dark:text-white truncate">
                                {pattern.merchant}
                              </h4>
                              {pattern.category && (
                                <p className="text-sm text-slate-600 dark:text-slate-400">
                                  {pattern.category}
                                </p>
                              )}
                            </div>
                            <Badge
                              variant={getConfidenceBadgeVariant(pattern.confidence)}
                              className="flex-shrink-0"
                            >
                              {pattern.confidence}%
                            </Badge>
                          </div>

                          {/* Details row */}
                          <div className="flex flex-wrap items-center gap-4 text-sm mt-3 text-slate-600 dark:text-slate-400">
                            <div className="flex items-center gap-1">
                              <DollarSign className="w-4 h-4" />
                              <span>
                                {formatCurrency(pattern.average_amount, "CAD")}
                                {pattern.amount_variance > 0 && (
                                  <span className="text-xs">
                                    {" "}
                                    ±{pattern.amount_variance.toFixed(2)}
                                  </span>
                                )}
                              </span>
                            </div>
                            <div>
                              <Badge variant="secondary" size="sm">
                                {getFrequencyLabel(pattern.frequency)}
                              </Badge>
                            </div>
                            {pattern.next_expected && (
                              <div className="flex items-center gap-1">
                                <Calendar className="w-4 h-4" />
                                <span>
                                  Next:{" "}
                                  {format(parseISO(pattern.next_expected), "MMM d")}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Right: Actions */}
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedPattern(pattern);
                              setIsDetailsModalOpen(true);
                            }}
                            title="View details"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedPattern(pattern);
                              setIsEditModalOpen(true);
                            }}
                            title="Edit pattern"
                          >
                            <Edit2 className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              if (pattern.id) {
                                setDeleteConfirmId(pattern.id);
                              }
                            }}
                            className="text-danger-600 hover:text-danger-700"
                            title="Delete pattern"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
          </div>
        </div>
      )}

      {/* Inactive patterns */}
      {patterns.filter((p) => !p.is_active).length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
            Inactive Patterns ({patterns.filter((p) => !p.is_active).length})
          </h3>
          <div className="space-y-3 opacity-60">
            {patterns
              .filter((p) => !p.is_active)
              .map((pattern, index) => (
                <motion.div
                  key={pattern.id || index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="border-dashed">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-semibold text-slate-900 dark:text-white">
                            {pattern.merchant}
                          </h4>
                          <p className="text-sm text-slate-600 dark:text-slate-400">
                            Inactive • {getFrequencyLabel(pattern.frequency)}
                          </p>
                        </div>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => {
                            if (pattern.id) {
                              onUpdate?.({
                                ...pattern,
                                is_active: true,
                              });
                            }
                          }}
                        >
                          Reactivate
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {selectedPattern && (
        <Modal
          isOpen={isEditModalOpen}
          onClose={() => {
            setIsEditModalOpen(false);
            setSelectedPattern(null);
          }}
          title="Edit Recurring Pattern"
        >
          <RecurringForm
            pattern={selectedPattern}
            onSave={(updatedPattern) => {
              onUpdate?.(updatedPattern);
              setIsEditModalOpen(false);
              setSelectedPattern(null);
            }}
            onCancel={() => {
              setIsEditModalOpen(false);
              setSelectedPattern(null);
            }}
          />
        </Modal>
      )}

      {/* Details Modal */}
      {selectedPattern && (
        <Modal
          isOpen={isDetailsModalOpen}
          onClose={() => {
            setIsDetailsModalOpen(false);
            setSelectedPattern(null);
          }}
          title={selectedPattern.merchant}
        >
          <RecurringCard pattern={selectedPattern} />
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={deleteConfirmId !== null}
        onClose={() => setDeleteConfirmId(null)}
        onConfirm={() => {
          if (deleteConfirmId) {
            onDelete?.(deleteConfirmId);
            setDeleteConfirmId(null);
          }
        }}
        title="Delete Recurring Pattern"
        description="Are you sure you want to delete this recurring pattern? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default RecurringList;
