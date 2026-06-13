import React, { useMemo, useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/components/ui/Toast";
import { Table } from "@/components/ui/Table";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ConfirmModal } from "@/components/ui/Modal";
import { Edit2, Trash2, AlertCircle, ArrowRight } from "lucide-react";
import { cn } from "@/utils/cn";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "");

export interface Budget {
  id: string;
  name: string;
  currency: string;
  description?: string;
  is_active: boolean;
  categories: Array<{
    id: string;
    category_id: string;
    limit_amount: number;
    period_type: string;
  }>;
  created_at: string;
  updated_at: string;
}

interface BudgetListProps {
  onEdit: (budget: Budget) => void;
}

export default function BudgetList({ onEdit }: BudgetListProps) {
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const { addToast } = useToast();
  const queryClient = useQueryClient();

  const { data: budgets = [], isLoading, error } = useQuery<Budget[]>({
    queryKey: ["budgets"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/budgets`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to load budgets");
      return res.json();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (budgetId: string) => {
      const res = await fetch(`${API_URL}/v1/budgets/${budgetId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to delete budget");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      addToast({
        variant: "success",
        title: "Budget deleted",
        description: "The budget has been successfully deleted.",
      });
      setDeleteConfirm(null);
    },
    onError: (err: Error) => {
      addToast({
        variant: "danger",
        title: "Delete failed",
        description: err.message,
      });
    },
  });

  const columns = [
    {
      id: "name",
      header: "Name",
      accessorKey: "name" as const,
      cell: (value: string, row: Budget) => (
        <div className="flex flex-col">
          <span className="font-medium text-slate-900 dark:text-white">
            {value}
          </span>
          {row.description && (
            <span className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              {row.description}
            </span>
          )}
        </div>
      ),
    },
    {
      id: "currency",
      header: "Currency",
      accessorKey: "currency" as const,
      cell: (value: string) => <Badge variant="secondary">{value}</Badge>,
    },
    {
      id: "categories",
      header: "Categories",
      accessorKey: "categories" as const,
      cell: (categories: Array<any>) => (
        <span className="text-sm text-slate-600 dark:text-slate-400">
          {categories.length} {categories.length === 1 ? "category" : "categories"}
        </span>
      ),
    },
    {
      id: "status",
      header: "Status",
      accessorKey: "is_active" as const,
      cell: (isActive: boolean) => (
        <Badge variant={isActive ? "success" : "secondary"}>
          {isActive ? "Active" : "Inactive"}
        </Badge>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (_: any, row: Budget) => (
        <div className="flex gap-2">
          <Link href={`/budgets/${row.id}`}>
            <Button
              variant="ghost"
              size="sm"
              rightIcon={<ArrowRight className="w-4 h-4" />}
              aria-label="View budget"
            >
              View
            </Button>
          </Link>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(row)}
            leftIcon={<Edit2 className="w-4 h-4" />}
            aria-label="Edit budget"
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setDeleteConfirm(row.id)}
            leftIcon={<Trash2 className="w-4 h-4 text-danger-600" />}
            aria-label="Delete budget"
          />
        </div>
      ),
    },
  ];

  if (error) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-lg bg-danger-50 dark:bg-danger-950/30 border border-danger-200 dark:border-danger-800">
        <AlertCircle className="w-5 h-5 text-danger-600 dark:text-danger-400 flex-shrink-0" />
        <div>
          <p className="text-sm font-medium text-danger-900 dark:text-danger-200">
            Failed to load budgets
          </p>
          <p className="text-sm text-danger-700 dark:text-danger-300">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Table
        data={budgets}
        columns={columns}
        emptyMessage="No budgets yet. Create your first budget to get started!"
        sortable
        striped
      />

      <ConfirmModal
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={() => deleteConfirm && deleteMutation.mutate(deleteConfirm)}
        title="Delete Budget"
        description="Are you sure you want to delete this budget? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </>
  );
}
