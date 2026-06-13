import React, { useState } from "react";
import { format, parseISO } from "date-fns";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { AlertCircle, Save, X } from "lucide-react";
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

interface RecurringFormProps {
  pattern: RecurringPattern;
  onSave: (pattern: RecurringPattern) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const FREQUENCY_OPTIONS = [
  { value: "weekly", label: "Weekly" },
  { value: "biweekly", label: "Biweekly (Every 2 weeks)" },
  { value: "monthly", label: "Monthly" },
  { value: "quarterly", label: "Quarterly" },
  { value: "annual", label: "Annually" },
];

const RecurringForm: React.FC<RecurringFormProps> = ({
  pattern,
  onSave,
  onCancel,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<RecurringPattern>(pattern);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (field: keyof RecurringPattern, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.merchant || formData.merchant.trim() === "") {
      newErrors.merchant = "Merchant is required";
    }

    if (formData.average_amount <= 0) {
      newErrors.average_amount = "Average amount must be greater than 0";
    }

    if (!formData.frequency) {
      newErrors.frequency = "Frequency is required";
    }

    if (formData.next_expected) {
      try {
        parseISO(formData.next_expected);
      } catch {
        newErrors.next_expected = "Invalid date format";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSave(formData);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Merchant Name */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
          Merchant Name
        </label>
        <Input
          type="text"
          value={formData.merchant}
          onChange={(e) => handleChange("merchant", e.target.value)}
          placeholder="e.g., Spotify, Netflix, Salary Deposit"
          disabled={isLoading}
          className={errors.merchant ? "border-red-500" : ""}
        />
        {errors.merchant && (
          <p className="text-xs text-red-600 dark:text-red-400 mt-1">
            {errors.merchant}
          </p>
        )}
      </div>

      {/* Category */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
          Category (Optional)
        </label>
        <Input
          type="text"
          value={formData.category || ""}
          onChange={(e) => handleChange("category", e.target.value || undefined)}
          placeholder="e.g., Subscriptions, Income"
          disabled={isLoading}
        />
      </div>

      {/* Amount Section */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Average Amount (CAD)
          </label>
          <Input
            type="number"
            step="0.01"
            min="0.01"
            value={formData.average_amount}
            onChange={(e) =>
              handleChange("average_amount", parseFloat(e.target.value))
            }
            placeholder="0.00"
            disabled={isLoading}
            className={errors.average_amount ? "border-red-500" : ""}
          />
          {errors.average_amount && (
            <p className="text-xs text-red-600 dark:text-red-400 mt-1">
              {errors.average_amount}
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Variance (±)
          </label>
          <Input
            type="number"
            step="0.01"
            min="0"
            value={formData.amount_variance}
            onChange={(e) =>
              handleChange("amount_variance", parseFloat(e.target.value))
            }
            placeholder="0.00"
            disabled={isLoading}
          />
          <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
            Tolerance for amount variation
          </p>
        </div>
      </div>

      {/* Frequency */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
          Frequency
        </label>
        <Select
          value={formData.frequency}
          onChange={(e) => handleChange("frequency", e.target.value)}
          disabled={isLoading}
          className={errors.frequency ? "border-red-500" : ""}
        >
          {FREQUENCY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </Select>
        {errors.frequency && (
          <p className="text-xs text-red-600 dark:text-red-400 mt-1">
            {errors.frequency}
          </p>
        )}
      </div>

      {/* Next Expected Date */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
          Next Expected Date (Optional)
        </label>
        <Input
          type="date"
          value={
            formData.next_expected
              ? format(parseISO(formData.next_expected), "yyyy-MM-dd")
              : ""
          }
          onChange={(e) => {
            if (e.target.value) {
              handleChange(
                "next_expected",
                new Date(e.target.value).toISOString()
              );
            } else {
              handleChange("next_expected", undefined);
            }
          }}
          disabled={isLoading}
          className={errors.next_expected ? "border-red-500" : ""}
        />
        {errors.next_expected && (
          <p className="text-xs text-red-600 dark:text-red-400 mt-1">
            {errors.next_expected}
          </p>
        )}
      </div>

      {/* Status */}
      <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="is_active"
            checked={formData.is_active}
            onChange={(e) => handleChange("is_active", e.target.checked)}
            disabled={isLoading}
            className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
          />
          <label
            htmlFor="is_active"
            className="text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Active Pattern
          </label>
        </div>
      </div>

      {/* Info Card */}
      <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <CardContent className="p-3">
          <div className="flex gap-2">
            <AlertCircle className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-blue-800 dark:text-blue-200">
              <p className="font-medium mb-1">
                Based on {formData.occurrences.length} detected occurrences
              </p>
              <p>
                Confidence: <Badge variant="primary">{formData.confidence}%</Badge>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Form Actions */}
      <div className="flex gap-3 pt-4 border-t border-slate-200 dark:border-slate-700">
        <Button
          type="submit"
          disabled={isLoading}
          className="flex-1 flex items-center justify-center gap-2"
        >
          <Save className="w-4 h-4" />
          Save Changes
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={isLoading}
          className="flex-1 flex items-center justify-center gap-2"
        >
          <X className="w-4 h-4" />
          Cancel
        </Button>
      </div>
    </form>
  );
};

export default RecurringForm;
