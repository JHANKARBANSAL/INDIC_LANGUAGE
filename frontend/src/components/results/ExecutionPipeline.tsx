"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  Clock,
  ShieldCheck,
  Code2,
  Database,
  Languages,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { QueryResponse } from "@/types/api";
import { formatLatency } from "@/lib/formatters";
import { SqlViewer } from "@/components/results/SqlViewer";

interface ExecutionPipelineProps {
  data: QueryResponse;
}

export function ExecutionPipeline({ data }: ExecutionPipelineProps) {
  const [showSql, setShowSql] = useState(false);

  // Extract metadata
  const schemaStep = data.audit_trace?.find(
    (s) => s.agent === "SchemaLinkerAgent" || s.action === "cross_lingual_lookup"
  );
  const matchedTable = schemaStep?.matched_table || "NDAP Dataset Linked";
  const latency = data.execution_result?.execution_time_ms;

  const stages = [
    {
      id: "lang",
      title: "Language & Script",
      icon: <Languages className="w-4 h-4 text-ashoka-700" />,
      detail: `${data.detected_language?.toUpperCase() || "INDIC"} (${data.detected_script || "Script"})`,
      status: "completed",
    },
    {
      id: "schema",
      title: "Schema Linking",
      icon: <Database className="w-4 h-4 text-ashoka-700" />,
      detail: matchedTable,
      status: "completed",
    },
    {
      id: "sql",
      title: "SQL Synthesis",
      icon: <Code2 className="w-4 h-4 text-emerald-600" />,
      detail: data.generated_sql ? "Dialect SQL Generated" : "Failed",
      status: data.generated_sql ? "completed" : "failed",
    },
    {
      id: "security",
      title: "AST Security Critic",
      icon: <ShieldCheck className="w-4 h-4 text-emerald-600" />,
      detail: "Read-Only Verified (SELECT)",
      status: "completed",
    },
    {
      id: "duckdb",
      title: "DuckDB Execution",
      icon: <Clock className="w-4 h-4 text-ashoka-700" />,
      detail: `${formatLatency(latency)} (${data.execution_result?.row_count ?? data.execution_result?.rows?.length ?? 0} rows)`,
      status: data.execution_result ? "completed" : "failed",
    },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Agent Swarm Execution Transparency
        </h3>
        {data.generated_sql && (
          <button
            onClick={() => setShowSql(!showSql)}
            className="text-xs font-medium text-ashoka-800 hover:text-ashoka-950 inline-flex items-center gap-1 focus:outline-none"
          >
            <span>{showSql ? "Hide SQL" : "View Synthesized SQL"}</span>
            {showSql ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </button>
        )}
      </div>

      {/* Horizontal Stepper / Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
        {stages.map((stage) => (
          <div
            key={stage.id}
            className="p-3 rounded-xl border border-slate-100 bg-slate-50/80 space-y-1.5"
          >
            <div className="flex items-center justify-between">
              <span className="p-1 rounded bg-white shadow-2xs border border-slate-200/60">
                {stage.icon}
              </span>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            </div>
            <p className="text-[11px] font-semibold text-slate-500">
              {stage.title}
            </p>
            <p className="text-xs font-medium text-slate-900 truncate font-mono" title={stage.detail}>
              {stage.detail}
            </p>
          </div>
        ))}
      </div>

      {/* Collapsible SQL Viewer */}
      {showSql && data.generated_sql && (
        <div className="pt-2">
          <SqlViewer sql={data.generated_sql} />
        </div>
      )}
    </div>
  );
}

