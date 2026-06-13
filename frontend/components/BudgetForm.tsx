import React, { useEffect, useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/components/ui/Toast";
import { Input, Textarea } from "@/components/ui/Input";
import { Select, MultiSelect, SelectOption } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Plus, Trash2 } from "lucide-react";
import { cn } from "@/utils/cn";
import { useFormState } from "@/hooks/useFormState";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "");

interface Category {
  id: string;
  name: string;
  group?: string;
}

interface BudgetCategoryRow {
  categoryId: string;
  categoryName: string;
  limitAmount: string;
  periodType: "MONTHLY" | "QUARTERLY" | "ANNUAL";
}

interface BudgetFormProps {
  budgetId?: string;
  initialData?: {
    name: string;
    currency: string;
    description?: string;
    isActive: boolean;
    categories?: BudgetCategoryRow[];
  };
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

export default function BudgetForm({
  budgetId,
  initialData,
  onSubmit,
  onCancel,
  loading = false,
}: BudgetFormProps) {
  const formKey = budgetId ? `budget_edit_${budgetId}` : "budget_create";
  const { getRecoveredState, saveFormState, clearFormState } =
    useFormState<any>(formKey, null);

  // Try to recover form state from sessionStorage first
  const recoveredState = getRecoveredState();

  const [name, setName] = useState(recoveredState?.name ?? initialData?.name ?? "");
  const [currency, setCurrency] = useState(
    recoveredState?.currency ?? initialData?.currency ?? "CAD"
  );
  const [description, setDescription] = useState(
    recoveredState?.description ?? initialData?.description ?? ""
  );
  const [isActive, setIsActive] = useState(
    recoveredState?.isActive ?? initialData?.isActive !== false
  );
  const [categoryRows, setCategoryRows] = useState<BudgetCategoryRow[]>(
    recoveredState?.categoryRows ?? initialData?.categories ?? []
  );
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showRecoveryNotice, setShowRecoveryNotice] = useState(!!recoveredState);
  const [showSuccess, setShowSuccess] = useState(false);
  const { addToast } = useToast();

  // Auto-save form state whenever it changes
  useEffect(() => {
    saveFormState({
      name,
      currency,
      description,
      isActive,
      categoryRows,
    });
  }, [name, currency, description, isActive, categoryRows, saveFormState]);

  // Fetch available categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ["transaction-categories"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/transaction-categories`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to load categories");
      return res.json();
    },
  });

  const categoryOptions: SelectOption[] = useMemo(
    () =>
      categories.map((cat) => ({
        value: cat.id,
        label: cat.name,
      })),
    [categories]
  );

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = "Budget name is required";
    }

    if (categoryRows.length === 0) {
      newErrors.categories = "At least one category limit is required";
    }

    categoryRows.forEach((row, idx) => {
      if (!row.categoryId) {
        newErrors[`category_${idx}`] = "Category is required";
      }
      if (!row.limitAmount || parseFloat(row.limitAmount) <= 0) {
        newErrors[`limit_${idx}`] = "Limit must be greater than 0";
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleAddCategory = () => {
    setCategoryRows([
      ...categoryRows,
      {
        categoryId: "",
        categoryName: "",
        limitAmount: "",
        periodType: "MONTHLY",
      },
    ]);
  };

  const handleRemoveCategory = (index: number) => {
    setCategoryRows(categoryRows.filter((_, i) => i !== index));
  };

  const handleCategoryChange = (index: number, categoryId: string) => {
    const category = categories.find((c) => c.id === categoryId);
    const updated = [...categoryRows];
    updated[index] = {
      ...updated[index],
      categoryId,
      categoryName: category?.name || "",
    };
    setCategoryRows(updated);
  };

  const handleLimitChange = (index: number, amount: string) => {
    const updated = [...categoryRows];
    updated[index].limitAmount = amount;
    setCategoryRows(updated);
  };

  const handlePeriodChange = (index: number, period: string) => {
    const updated = [...categoryRows];
    updated[index].periodType = period as "MONTHLY" | "QUARTERLY" | "ANNUAL";
    setCategoryRows(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      addToast({
        variant: "danger",
        title: "Validation error",
        description: "Please check the form for errors",
      });
      return;
    }

    try {
      const payload = {
        name,
        currency,
        description: description || null,
        is_active: isActive,
        categories: categoryRows.map((row) => ({
          category_id: row.categoryId,
          limit_amount: parseFloat(row.limitAmount),
          period_type: row.periodType,
          rollover_excess: false,
        })),
      };

      await onSubmit(payload);
      // Show success state briefly
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 1500);
      // Clear saved form state on successful submission
      clearFormState();
      setShowRecoveryNotice(false);
    } catch (err) {
      console.error("Error submitting budget:", err);
      // Form state remains saved for recovery on retry
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Recovery Notice */}
      {showRecoveryNotice && (
        <div className="p-3 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg flex items-center justify-between">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            <span className="font-semibold">✓ Recovered</span> Your previous form data has been restored.
          </p>
          <button
            type="button"
            onClick={() => setShowRecoveryNotice(false)}
            className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-200 text-sm"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Basic Info */}
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-slate-900 dark:text-white">
          Budget Information
        </h3>

        <Input
          label="Budget Name"
          placeholder="e.g., Monthly Essentials"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.name}
        />

        <Select
          label="Currency"
          options={[
            { value: "CAD", label: "CAD - Canadian Dollar" },
            { value: "USD", label: "USD - US Dollar" },
          ]}
          value={currency}
          onChange={setCurrency}
        />

        <Textarea
          label="Description (optional)"
          placeholder="Add notes about this budget..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
        />

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="text-sm text-slate-700 dark:text-slate-300">
            Active
          </span>
        </label>
      </div>

      {/* Category Limits */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-slate-900 dark:text-white">
            Category Limits
          </h3>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleAddCategory}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Add Category
          </Button>
        </div>

        {errors.categories && (
          <p className="text-xs text-danger-600 dark:text-danger-400">
            {errors.categories}
          </p>
        )}

        <div className="space-y-3 max-h-96 overflow-auto">
          {categoryRows.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400 italic">
              No categories added yet. Click &quot;Add Category&quot; to get started.
            </p>
          ) : (
            categoryRows.map((row, idx) => (
              <Card
                key={idx}
                className="p-4 border-slate-200 dark:border-slate-800"
              >
                <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
                  <Select
                    label="Category"
                    options={categoryOptions}
                    value={row.categoryId}
                    onChange={(val) => handleCategoryChange(idx, val)}
                    placeholder="Select category"
                    className="md:col-span-2"
                  />

                  <Input
                    label="Limit Amount"
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="0.00"
                    value={row.limitAmount}
                    onChange={(e) => handleLimitChange(idx, e.target.value)}
                    error={errors[`limit_${idx}`]}
                  />

                  <div className="flex items-end gap-2">
                    <Select
                      label="Period"
                      options={[
                        { value: "MONTHLY", label: "Monthly" },
                        { value: "QUARTERLY", label: "Quarterly" },
                        { value: "ANNUAL", label: "Annual" },
                      ]}
                      value={row.periodType}
                      onChange={(val) => handlePeriodChange(idx, val)}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="md"
                      onClick={() => handleRemoveCategory(idx)}
                      aria-label="Remove category"
                    >
                      <Trash2 className="w-4 h-4 text-danger-600" />
                    </Button>
                  </div>
                </div>

                {errors[`category_${idx}`] && (
                  <p className="text-xs text-danger-600 dark:text-danger-400 mt-2">
                    {errors[`category_${idx}`]}
                  </p>
                )}
              </Card>
            ))
          )}
        </div>
      </div>

      {/* Form Actions */}
      <div className="flex gap-3 justify-end pt-4 border-t border-slate-200 dark:border-slate-800">
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={loading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="primary"
          loading={loading}
          loadingText={budgetId ? "Updating..." : "Creating..."}
          successText={budgetId ? "Updated ✓" : "Created ✓"}
          showSuccess={showSuccess && !loading}
        >
          {budgetId ? "Update Budget" : "Create Budget"}
        </Button>
      </div>
    </form>
  );
}
