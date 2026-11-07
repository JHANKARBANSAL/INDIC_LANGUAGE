"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { detectChartType } from "@/lib/chart-utils";
import { formatCompactIndian, formatIndianNumber } from "@/lib/formatters";

interface ChartRendererProps {
  columns: string[];
  rows: (string | number | boolean | null)[][];
}

export function ChartRenderer({ columns, rows }: ChartRendererProps) {
  const chartInfo = detectChartType(columns, rows);

  if (chartInfo.chartType === "none" || !rows || rows.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-slate-400">
        No chartable numeric series detected in this tabular result.
      </div>
    );
  }

  // Single scalar result -> KPI Card
  if (chartInfo.chartType === "kpi") {
    const rawVal = chartInfo.kpiValue;
    const numVal = typeof rawVal === "number" ? rawVal : Number(rawVal);
    const compactText = !isNaN(numVal) ? formatCompactIndian(numVal) : String(rawVal);
    const fullText = !isNaN(numVal) ? formatIndianNumber(numVal) : "";

    return (
      <div className="py-8 flex flex-col items-center justify-center text-center space-y-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {chartInfo.kpiLabel || "Metric Result"}
        </span>
        <div className="text-4xl sm:text-5xl font-extrabold text-ashoka-950 font-mono tracking-tight">
          {compactText}
        </div>
        {fullText && fullText !== compactText && (
          <span className="text-xs text-slate-500 font-mono">
            Exact value: {fullText}
          </span>
        )}
      </div>
    );
  }

  const categoryKey = chartInfo.categoryKey || "category";
  const dataKey = chartInfo.dataKey || "value";
  const data = chartInfo.data;

  return (
    <div className="w-full h-72 sm:h-80 pt-4">
      <ResponsiveContainer width="100%" height="100%">
        {chartInfo.chartType === "line" ? (
          <LineChart data={data} margin={{ top: 10, right: 30, left: 10, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey={categoryKey}
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              dy={10}
            />
            <YAxis
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              tickFormatter={(v) => formatCompactIndian(v)}
            />
            <Tooltip
              formatter={(value: unknown) => [
                formatIndianNumber(Number(value)),
                dataKey.replace(/_/g, " "),
              ]}
              labelStyle={{ fontWeight: "bold", color: "#0f2942" }}
              contentStyle={{
                backgroundColor: "#ffffff",
                borderColor: "#e2e8f0",
                borderRadius: "8px",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
              }}
            />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke="#0f2942"
              strokeWidth={2.5}
              dot={{ r: 4, fill: "#059669" }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        ) : (
          <BarChart data={data} margin={{ top: 10, right: 30, left: 10, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey={categoryKey}
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              dy={10}
            />
            <YAxis
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              tickFormatter={(v) => formatCompactIndian(v)}
            />
            <Tooltip
              formatter={(value: unknown) => [
                formatIndianNumber(Number(value)),
                dataKey.replace(/_/g, " "),
              ]}
              labelStyle={{ fontWeight: "bold", color: "#0f2942" }}
              contentStyle={{
                backgroundColor: "#ffffff",
                borderColor: "#e2e8f0",
                borderRadius: "8px",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
              }}
            />
            <Bar dataKey={dataKey} fill="#1e3a5f" radius={[4, 4, 0, 0]} />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
