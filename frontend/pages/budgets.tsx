import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/router";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";
import BudgetForm from "@/components/BudgetForm";
import BudgetList, { Budget } from "@/components/BudgetList";
import { BudgetStatsSkeleton } from "@/components/ui/Skeleton";
import {
  BarChart3,
  Plus,
  AlertCircle,
  Loader2,
} from "lucide-react";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "");

interface BudgetStats {
  total_budgets: number;
  active_budgets: number;
  total_categories: number;
}

export default function BudgetsPage() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingBudget, setEditingBudget] = useState<Budget | null>(null);
  const [isFormLoading, setIsFormLoading] = useState(false);

  const { addToast } = useToast();
  const queryClient = useQueryClient();
  const router = useRouter();

  // Fetch budget stats
  const { data: stats } = useQuery<BudgetStats>({
    queryKey: ["budget-stats"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/v1/budgets/stats`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to load stats");
      return res.json();
    },
    retry: 1,
  });

  // Create budget mutation
  const createMutation = useMutation({
    mutationFn: async (payload: any) => {
      const res = await fetch(`${API_URL}/v1/budgets`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to create budget (${res.status})`);
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["budget-stats"] });
      addToast({
        variant: "success",
        title: "Budget created",
        description: "Your budget has been successfully created.",
      });
      setIsCreateModalOpen(false);
    },
    onError: (err: Error) => {
      addToast({
        variant: "danger",
        title: "Creation failed",
        description: err.message,
      });
    },
  });

  // Update budget mutation
  const updateMutation = useMutation({
    mutationFn: async (payload: any) => {
      if (!editingBudget) throw new Error("No budget selected");
      const res = await fetch(`${API_URL}/v1/budgets/${editingBudget.id}`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to update budget (${res.status})`);
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["budget-stats"] });
      addToast({
        variant: "success",
        title: "Budget updated",
        description: "Your budget has been successfully updated.",
      });
      setIsEditModalOpen(false);
      setEditingBudget(null);
    },
    onError: (err: Error) => {
      addToast({
        variant: "danger",
        title: "Update failed",
        description: err.message,
      });
    },
  });

  const handleEditBudget = (budget: Budget) => {
    setEditingBudget(budget);
    setIsEditModalOpen(true);
  };

  const handleCreateSubmit = async (data: any) => {
    setIsFormLoading(true);
    try {
      await createMutation.mutateAsync(data);
    } finally {
      setIsFormLoading(false);
    }
  };

  const handleUpdateSubmit = async (data: any) => {
    setIsFormLoading(true);
    try {
      await updateMutation.mutateAsync(data);
    } finally {
      setIsFormLoading(false);
    }
  };

  const handleCloseModal = () => {
    setIsCreateModalOpen(false);
    setIsEditModalOpen(false);
    setEditingBudget(null);
  };

  return (
    <PageLayout title="Budgets" description="Manage your spending budgets">
      {/* Page Header */}
      <PageHeader
        title="Budgets"
        description="Set spending limits for different categories and track your progress"
        actions={
          <Button
            variant="primary"
            onClick={() => setIsCreateModalOpen(true)}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            New Budget
          </Button>
        }
      />

      {/* Stats Cards */}
      {!stats ? (
        <BudgetStatsSkeleton />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    Total Budgets
                  </p>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1">
                    {stats.total_budgets}
                  </p>
                </div>
                <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    Active
                  </p>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1">
                    {stats.active_budgets}
                  </p>
                </div>
                <div className="w-12 h-12 bg-success-100 dark:bg-success-900/30 rounded-lg flex items-center justify-center">
                  <span className="text-lg font-bold text-success-600 dark:text-success-400">
                    ✓
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    Categories Tracked
                  </p>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1">
                    {stats.total_categories}
                  </p>
                </div>
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                  <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                    📊
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Budget List Section */}
      <div>
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
          Your Budgets
        </h2>
        <BudgetList onEdit={handleEditBudget} />
      </div>

      {/* Create Budget Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={handleCloseModal}
        title="Create New Budget"
        description="Set up a new budget with spending limits for specific categories"
        size="lg"
      >
        <BudgetForm
          onSubmit={handleCreateSubmit}
          onCancel={handleCloseModal}
          loading={isFormLoading}
        />
      </Modal>

      {/* Edit Budget Modal */}
      {editingBudget && (
        <Modal
          isOpen={isEditModalOpen}
          onClose={handleCloseModal}
          title="Edit Budget"
          description={`Update budget: ${editingBudget.name}`}
          size="lg"
        >
          <BudgetForm
            budgetId={editingBudget.id}
            initialData={{
              name: editingBudget.name,
              currency: editingBudget.currency,
              description: editingBudget.description,
              isActive: editingBudget.is_active,
              categories: editingBudget.categories.map((cat) => ({
                categoryId: cat.category_id,
                categoryName: cat.category_id,
                limitAmount: cat.limit_amount.toString(),
                periodType: cat.period_type as "MONTHLY" | "QUARTERLY" | "ANNUAL",
              })),
            }}
            onSubmit={handleUpdateSubmit}
            onCancel={handleCloseModal}
            loading={isFormLoading}
          />
        </Modal>
      )}
    </PageLayout>
  );
}
