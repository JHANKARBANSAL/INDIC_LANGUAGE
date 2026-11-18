"use client";

import React from "react";
import { AlertCircle, CheckCircle2, XCircle } from "lucide-react";
import { QueryResponse } from "@/types/api";
import { AnswerCard } from "@/components/results/AnswerCard";
import { ExecutionPipeline } from "@/components/results/ExecutionPipeline";
import { DataExplorer } from "@/components/results/DataExplorer";
import { Skeleton } from "@/components/ui/Skeleton";

interface ResultsWorkspaceProps {
  data: QueryResponse | null;
  isLoading: boolean;
  error: string | null;
  onSuggestedQuery: (query: string) => void;
}

export function ResultsWorkspace({
  data,
  isLoading,
  error,
  onSuggestedQuery,
}: ResultsWorkspaceProps) {
  if (isLoading) {
    return (
      <div className="w-full max-w-4xl mx-auto space-y-4 pt-4">
        {/* Answer Skeleton */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 space-y-3">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-7 w-full" />
          <Skeleton className="h-7 w-3/4" />
        </div>
        {/* Pipeline Skeleton */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-3">
          <Skeleton className="h-4 w-40" />
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-16 rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full max-w-4xl mx-auto pt-4">
        <div className="bg-red-50 border border-red-200 rounded-2xl p-5 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-red-900">
              Query Execution Error
            </h4>
            <p className="text-xs sm:text-sm text-red-700 leading-relaxed">
              {error}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  if (data.suggested_queries?.length) {
    return (
      <div className="w-full max-w-4xl mx-auto space-y-5 pt-2">
        <div
          role="status"
          aria-live="polite"
          className="rounded-2xl border border-amber-200 bg-amber-50 p-5"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" />
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-amber-950">
                Available data can't answer that exact question
              </h3>
              <p className="text-sm leading-relaxed text-amber-900">
                {data.execution_error || data.verbalized_response}
              </p>
              <p className="pt-1 text-sm font-medium text-slate-800">
                Try one of these supported questions:
              </p>
              <div className="flex flex-wrap gap-2">
                {data.suggested_queries.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => onSuggestedQuery(suggestion)}
                    className="rounded-xl border border-amber-300 bg-white px-3 py-2 text-left text-sm text-ashoka-900 transition-colors hover:bg-amber-100 focus:outline-none focus:ring-2 focus:ring-ashoka-700"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
        <ExecutionPipeline data={data} />
      </div>
    );
  }

  const executionSucceeded =
    data.execution_result !== null || data.execution_status === "success";
  const rowCount =
    data.execution_result?.row_count ?? data.execution_result?.rows.length ?? 0;

  return (
    <div className="w-full max-w-4xl mx-auto space-y-5 pt-2">
      {/* Card 1: Primary Natural Language Answer */}
      <AnswerCard data={data} />

      <div
        role="status"
        aria-live="polite"
        className={`flex items-start gap-3 rounded-2xl border p-4 ${
          executionSucceeded
            ? "border-emerald-200 bg-emerald-50 text-emerald-950"
            : "border-red-200 bg-red-50 text-red-950"
        }`}
      >
        {executionSucceeded ? (
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-700" />
        ) : (
          <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-700" />
        )}
        <div className="space-y-1">
          <h3 className="text-sm font-semibold">
            {executionSucceeded
              ? `SQL executed; ${rowCount} ${
                  rowCount === 1 ? "row" : "rows"
                } returned`
              : "SQL did not execute successfully"}
          </h3>
          {!executionSucceeded && (
            <p className="break-words text-sm text-red-800">
              {data.execution_error || "No execution result was returned."}
            </p>
          )}
          <p className="text-xs text-slate-600">
            Successful execution confirms the query ran; it does not prove the
            answer is semantically correct. Compare the returned rows with an
            expected result to verify correctness.
          </p>
          {data.applied_defaults?.map((appliedDefault) => (
            <p
              key={appliedDefault}
              className="text-xs font-medium text-amber-800"
            >
              Assumption applied: {appliedDefault}
            </p>
          ))}
        </div>
      </div>

      {/* Card 2: Swarm Execution Pipeline & SQL */}
      <ExecutionPipeline data={data} />

      {/* Card 3: Dynamic Data Explorer & Visualization */}
      <DataExplorer
        executionResult={data.execution_result}
        queryId={data.query_id}
      />
    </div>
  );
}

