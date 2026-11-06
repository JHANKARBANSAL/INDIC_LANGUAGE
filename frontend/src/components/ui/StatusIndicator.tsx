import React from "react";
import { clsx } from "clsx";

interface StatusIndicatorProps {
  status: "connected" | "disconnected" | "checking";
  tableCount?: number;
}

export function StatusIndicator({ status, tableCount }: StatusIndicatorProps) {
  if (status === "checking") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
        <span className="w-2 h-2 rounded-full bg-slate-400 animate-pulse" />
        Checking backend...
      </span>
    );
  }

  if (status === "connected") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
        <span className="w-2 h-2 rounded-full bg-emerald-600" />
        Backend Connected {tableCount !== undefined ? `(${tableCount} DBs)` : ""}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200">
      <span className="w-2 h-2 rounded-full bg-amber-500" />
      Backend Disconnected (localhost:8000)
    </span>
  );
}

