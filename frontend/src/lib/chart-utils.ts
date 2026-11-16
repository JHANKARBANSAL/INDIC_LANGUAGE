import { ExecutionResult } from "@/types/api";

type ChartRow = Record<string, string | number | boolean | null>;

export type ChartInfo =
  | { chartType: "none" }
  | { chartType: "kpi"; kpiLabel: string; kpiValue: number }
  | {
      chartType: "bar" | "line";
      categoryKey: string;
      dataKey: string;
      data: ChartRow[];
    };

function numericValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function detectChartType(
  columns: string[],
  rows: ExecutionResult["rows"]
): ChartInfo {
  if (columns.length === 0 || rows.length === 0) return { chartType: "none" };

  const numericColumns = columns
    .map((column, index) => ({
      column,
      index,
      values: rows.map((row) => numericValue(row[index])),
    }))
    .filter(({ values }) => values.some((value) => value !== null));

  if (numericColumns.length === 0) return { chartType: "none" };
  if (rows.length === 1 && numericColumns.length === 1) {
    const metric = numericColumns[0];
    const value = metric.values[0];
    return value === null
      ? { chartType: "none" }
      : { chartType: "kpi", kpiLabel: metric.column, kpiValue: value };
  }

  const metric = numericColumns[0];
  const categoryColumn = columns.find(
    (_, index) => index !== metric.index && rows.some((row) => row[index] !== null)
  );
  const categoryKey = categoryColumn || "row";
  const data = rows.map((row, rowIndex) => ({
    [categoryKey]: categoryColumn ? row[columns.indexOf(categoryColumn)] : rowIndex + 1,
    [metric.column]: numericValue(row[metric.index]),
  }));
  const chartType = /year|month|date|time/i.test(categoryKey) ? "line" : "bar";

  return {
    chartType,
    categoryKey,
    dataKey: metric.column,
    data,
  };
}
