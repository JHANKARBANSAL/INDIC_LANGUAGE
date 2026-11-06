"use client";

import React, { useState } from "react";
import { Check, Copy, Code2, ChevronDown, ChevronUp } from "lucide-react";

interface SqlViewerProps {
  sql: string;
}

export function SqlViewer({ sql }: SqlViewerProps) {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  if (!sql) return null;

  return (
    <div className="border border-slate-200 rounded-xl bg-slate-900 text-slate-100 overflow-hidden shadow-sm">
      {/* Header Bar */}
      <div className="px-4 py-2.5 bg-slate-800/80 border-b border-slate-700/60 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <Code2 className="w-4 h-4 text-emerald-400" />
          <span className="font-mono font-medium text-slate-200">
            Synthesized Dialect SQL (DuckDB Engine)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white transition-colors"
            title="Copy SQL Query"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 font-medium">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy SQL</span>
              </>
            )}
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-200"
            aria-label={isExpanded ? "Collapse SQL" : "Expand SQL"}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Code Body */}
      <div
        className={`p-4 font-mono text-xs sm:text-sm leading-relaxed overflow-x-auto transition-all ${
          isExpanded ? "max-h-96" : "max-h-24"
        }`}
      >
        <pre className="text-emerald-300 font-mono whitespace-pre-wrap break-all">
          {sql}
        </pre>
      </div>
    </div>
  );
}

