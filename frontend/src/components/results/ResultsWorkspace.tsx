"use client";

import React from "react";
import { AlertCircle } from "lucide-react";
import { QueryResponse } from "@/types/api";
import { AnswerCard } from "@/components/results/AnswerCard";
import { ExecutionPipeline } from "@/components/results/ExecutionPipeline";
import { DataExplorer } from "@/components/results/DataExplorer";
import { Skeleton } from "@/components/ui/Skeleton";

interface ResultsWorkspaceProps {
  data: QueryResponse | null;
  isLoading: boolean;
  error: string | null;
}

export function ResultsWorkspace({
  data,
  isLoading,
  error,
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

  return (
    <div className="w-full max-w-4xl mx-auto space-y-5 pt-2">
      {/* Card 1: Primary Natural Language Answer */}
      <AnswerCard data={data} />

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

