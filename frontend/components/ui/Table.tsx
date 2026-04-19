import React, { useState, useMemo, useCallback } from "react";
import { ChevronUp, ChevronDown, ChevronsUpDown, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/utils/cn";

export type SortDirection = "asc" | "desc" | null;

export interface ColumnDef<T> {
  id: string;
  header: string;
  accessorFn?: (row: T) => any;
  accessorKey?: keyof T;
  cell?: (value: any, row: T) => React.ReactNode;
  sortable?: boolean;
  className?: string;
  headerClassName?: string;
  align?: "left" | "center" | "right";
}

export interface TableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  pageSize?: number;
  sortable?: boolean;
  striped?: boolean;
  compact?: boolean;
  stickyHeader?: boolean;
  emptyMessage?: string;
  className?: string;
  onRowClick?: (row: T, index: number) => void;
  rowClassName?: (row: T, index: number) => string;
  getRowKey?: (row: T, index: number) => string | number;
}

function getCellValue<T>(row: T, column: ColumnDef<T>): any {
  if (column.accessorFn) return column.accessorFn(row);
  if (column.accessorKey) return row[column.accessorKey];
  return undefined;
}

export function Table<T>({
  data,
  columns,
  pageSize = 0,
  sortable = false,
  striped = false,
  compact = false,
  stickyHeader = false,
  emptyMessage = "No data to display",
  className,
  onRowClick,
  rowClassName,
  getRowKey,
}: TableProps<T>) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [currentPage, setCurrentPage] = useState(1);

  const handleSort = useCallback(
    (columnId: string) => {
      if (sortColumn === columnId) {
        if (sortDirection === "asc") setSortDirection("desc");
        else if (sortDirection === "desc") {
          setSortColumn(null);
          setSortDirection(null);
        }
      } else {
        setSortColumn(columnId);
        setSortDirection("asc");
      }
      setCurrentPage(1);
    },
    [sortColumn, sortDirection]
  );

  const sortedData = useMemo(() => {
    if (!sortColumn || !sortDirection) return data;

    const column = columns.find((c) => c.id === sortColumn);
    if (!column) return data;

    return [...data].sort((a, b) => {
      const aVal = getCellValue(a, column);
      const bVal = getCellValue(b, column);

      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;

      let result: number;
      if (typeof aVal === "number" && typeof bVal === "number") {
        result = aVal - bVal;
      } else if (aVal instanceof Date && bVal instanceof Date) {
        result = aVal.getTime() - bVal.getTime();
      } else {
        result = String(aVal).localeCompare(String(bVal));
      }

      return sortDirection === "desc" ? -result : result;
    });
  }, [data, sortColumn, sortDirection, columns]);

  const paginatedData = useMemo(() => {
    if (pageSize <= 0) return sortedData;
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize]);

  const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(data.length / pageSize)) : 1;
  const showPagination = pageSize > 0 && totalPages > 1;

  const cellPadding = compact ? "px-3 py-2" : "px-4 py-3";
  const headerPadding = compact ? "px-3 py-2" : "px-4 py-3";

  return (
    <div className={cn("w-full", className)}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr
              className={cn(
                "border-b border-slate-200 dark:border-slate-800",
                stickyHeader && "sticky top-0 z-10 bg-white dark:bg-slate-900"
              )}
            >
              {columns.map((column) => {
                const isSortable = sortable && column.sortable !== false;
                const isSorted = sortColumn === column.id;
                const align = column.align ?? "left";

                return (
                  <th
                    key={column.id}
                    className={cn(
                      headerPadding,
                      "text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider",
                      "bg-slate-50/80 dark:bg-slate-900/80",
                      align === "right" && "text-right",
                      align === "center" && "text-center",
                      isSortable && "cursor-pointer select-none hover:text-slate-700 dark:hover:text-slate-300 transition-colors",
                      column.headerClassName
                    )}
                    onClick={isSortable ? () => handleSort(column.id) : undefined}
                  >
                    <span className="inline-flex items-center gap-1">
                      {column.header}
                      {isSortable && (
                        <span className="inline-flex">
                          {isSorted ? (
                            sortDirection === "asc" ? (
                              <ChevronUp className="w-3.5 h-3.5" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5" />
                            )
                          ) : (
                            <ChevronsUpDown className="w-3.5 h-3.5 opacity-40" />
                          )}
                        </span>
                      )}
                    </span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-12 text-center text-slate-400 dark:text-slate-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, rowIndex) => {
                const globalIndex =
                  pageSize > 0 ? (currentPage - 1) * pageSize + rowIndex : rowIndex;
                const key = getRowKey ? getRowKey(row, globalIndex) : globalIndex;

                return (
                  <tr
                    key={key}
                    onClick={onRowClick ? () => onRowClick(row, globalIndex) : undefined}
                    className={cn(
                      "transition-colors",
                      onRowClick && "cursor-pointer",
                      "hover:bg-slate-50 dark:hover:bg-slate-800/50",
                      striped && rowIndex % 2 === 1 && "bg-slate-50/50 dark:bg-slate-800/20",
                      rowClassName?.(row, globalIndex)
                    )}
                  >
                    {columns.map((column) => {
                      const value = getCellValue(row, column);
                      const align = column.align ?? "left";

                      return (
                        <td
                          key={column.id}
                          className={cn(
                            cellPadding,
                            "text-slate-700 dark:text-slate-300",
                            align === "right" && "text-right",
                            align === "center" && "text-center",
                            column.className
                          )}
                        >
                          {column.cell ? column.cell(value, row) : (value ?? "—")}
                        </td>
                      );
                    })}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {showPagination && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200 dark:border-slate-800">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Showing{" "}
            <span className="font-medium text-slate-700 dark:text-slate-300">
              {(currentPage - 1) * pageSize + 1}
            </span>
            {" "}to{" "}
            <span className="font-medium text-slate-700 dark:text-slate-300">
              {Math.min(currentPage * pageSize, data.length)}
            </span>
            {" "}of{" "}
            <span className="font-medium text-slate-700 dark:text-slate-300">
              {data.length}
            </span>
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className={cn(
                "p-1.5 rounded-md transition-colors",
                "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300",
                "hover:bg-slate-100 dark:hover:bg-slate-800",
                "disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
              )}
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              let page: number;
              if (totalPages <= 5) {
                page = i + 1;
              } else if (currentPage <= 3) {
                page = i + 1;
              } else if (currentPage >= totalPages - 2) {
                page = totalPages - 4 + i;
              } else {
                page = currentPage - 2 + i;
              }

              return (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={cn(
                    "w-8 h-8 rounded-md text-sm font-medium transition-colors",
                    page === currentPage
                      ? "bg-primary-50 text-primary-700 dark:bg-primary-950/50 dark:text-primary-300"
                      : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                  )}
                >
                  {page}
                </button>
              );
            })}
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className={cn(
                "p-1.5 rounded-md transition-colors",
                "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300",
                "hover:bg-slate-100 dark:hover:bg-slate-800",
                "disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
              )}
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
