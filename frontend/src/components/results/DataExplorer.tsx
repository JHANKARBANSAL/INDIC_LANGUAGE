"use client";

import React, { useState } from "react";
import { BarChart3, Table as TableIcon, Download } from "lucide-react";
import { Tabs } from "@/components/ui/Tabs";
import { ChartRenderer } from "@/components/results/ChartRenderer";
import { DataTable } from "@/components/results/DataTable";
import { exportToCSV } from "@/lib/csv-export";
import { ExecutionResult } from "@/types/api";

interface DataExplorerProps {
  executionResult: ExecutionResult | null;
  queryId?: string;
}

export function DataExplorer({ executionResult, queryId }: DataExplorerProps) {
  const [activeTab, setActiveTab] = useState<string>("chart");
  const [exportError, setExportError] = useState<string | null>(null);

  if (!executionResult || !executionResult.columns || executionResult.columns.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-6 text-center text-sm text-slate-400">
        No execution data available for this query.
      </div>
    );
  }

  const { columns, rows } = executionResult;

  const handleExportCSV = () => {
    setExportError(null);
    try {
      const filename = `bharatquery_${queryId || Date.now()}.csv`;
      exportToCSV(columns, rows, filename);
    } catch (err: unknown) {
      setExportError(
        err instanceof Error ? err.message : "Failed to export CSV file."
      );
    }
  };

  const tabs = [
    {
      id: "chart",
      label: "Visual Chart",
      icon: <BarChart3 className="w-4 h-4" />,
    },
    {
      id: "table",
      label: `Data Table (${rows.length})`,
      icon: <TableIcon className="w-4 h-4" />,
    },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
      {/* Tab Header & CSV Export */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

        <button
          onClick={handleExportCSV}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 transition-colors shadow-2xs"
          title="Export returned rows to CSV file"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download CSV</span>
        </button>
      </div>

      {exportError && (
        <div className="p-2 text-xs text-red-700 bg-red-50 border border-red-200 rounded">
          {exportError}
        </div>
      )}

      {/* Tab Content */}
      <div role="tabpanel" id={`panel-${activeTab}`} aria-labelledby={`tab-${activeTab}`}>
        {activeTab === "chart" ? (
          <ChartRenderer columns={columns} rows={rows} />
        ) : (
          <DataTable columns={columns} rows={rows} />
        )}
      </div>
    </div>
  );
}

