export function formatIndianNumber(
  value: number | string | null | undefined
): string {
  if (value === null || value === undefined || value === "") return "—";
  const numericValue = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numericValue)) return String(value);
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 2,
  }).format(numericValue);
}

export function formatCompactIndian(value: number | string): string {
  const numericValue = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numericValue)) return String(value);
  const absoluteValue = Math.abs(numericValue);
  if (absoluteValue >= 10_000_000) {
    return `${(numericValue / 10_000_000).toFixed(2)} Cr`;
  }
  if (absoluteValue >= 100_000) {
    return `${(numericValue / 100_000).toFixed(2)} L`;
  }
  return formatIndianNumber(numericValue);
}

export function formatLatency(milliseconds?: number): string {
  if (milliseconds === undefined || !Number.isFinite(milliseconds)) return "—";
  if (milliseconds < 1000) {
    return `${milliseconds.toFixed(milliseconds < 10 ? 1 : 0)} ms`;
  }
  return `${(milliseconds / 1000).toFixed(2)} s`;
}
