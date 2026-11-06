"use client";

import React, { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { formatIndianNumber } from "@/lib/formatters";

interface DataTableProps {
  columns: string[];
  rows: (string | number | boolean | null)[][];
}

const PAGE_SIZE = 10;

export function DataTable({ columns, rows }: DataTableProps) {
  const [currentPage, setCurrentPage] = useState(1);

  if (!columns || columns.length === 0 || !rows || rows.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-slate-400">
        No records returned by database engine.
      </div>
    );
  }

  const totalPages = Math.ceil(rows.length / PAGE_SIZE);
  const startIndex = (currentPage - 1) * PAGE_SIZE;
  const currentRows = rows.slice(startIndex, startIndex + PAGE_SIZE);

  return (
    <div className="space-y-3">
      {/* Scrollable Table Container */}
      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="w-full text-left text-xs sm:text-sm border-collapse">
          <thead>
            <tr className="bg-slate-100/80 border-b border-slate-200 text-slate-700 font-semibold">
              <th className="py-2.5 px-3 w-12 text-center text-slate-400 font-mono text-xs">
                #
              </th>
              {columns.map((col, idx) => (
                <th key={idx} className="py-2.5 px-4 font-mono font-medium text-slate-800">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {currentRows.map((row, rIdx) => (
              <tr
                key={rIdx}
                className={rIdx % 2 === 0 ? "bg-white" : "bg-slate-50/50 hover:bg-slate-50"}
              >
                <td className="py-2.5 px-3 text-center text-slate-400 font-mono text-xs">
                  {startIndex + rIdx + 1}
                </td>
                {columns.map((_, cIdx) => {
                  const cell = row[cIdx];
                  const isNum = typeof cell === "number";
                  return (
                    <td
                      key={cIdx}
                      className={`py-2.5 px-4 font-mono text-slate-800 ${
                        isNum ? "text-right" : "text-left"
                      }`}
                    >
                      {cell === null || cell === undefined
                        ? "—"
                        : isNum
                        ? formatIndianNumber(cell)
                        : String(cell)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Bar */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-1 text-xs text-slate-500">
          <span>
            Showing {startIndex + 1} to {Math.min(startIndex + PAGE_SIZE, rows.length)} of{" "}
            {rows.length} rows
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="Previous Page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono px-2">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="Next Page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

