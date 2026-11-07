"use client";

import React, { useEffect, useState } from "react";
import { X, Search, Database, Layers, CheckCircle2, ChevronRight } from "lucide-react";
import { SchemasResponse } from "@/types/api";
import { KNOWN_SECTOR_MAPPINGS, SectorType } from "@/types/datasets";

interface DatabaseDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  schemas: SchemasResponse | null;
  isLoading: boolean;
}

const SECTORS: Array<"All" | SectorType> = [
  "All",
  "Agriculture",
  "Education",
  "Health and Demographics",
  "Rural Development",
];

export function DatabaseDrawer({
  isOpen,
  onClose,
  schemas,
  isLoading,
}: DatabaseDrawerProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSector, setSelectedSector] = useState<"All" | SectorType>("All");
  const [expandedTable, setExpandedTable] = useState<string | null>(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const tables = schemas?.tables ? Object.values(schemas.tables) : [];

  // Filter tables by search term and sector
  const filteredTables = tables.filter((tbl) => {
    const sector =
      (tbl.domain as SectorType) ||
      KNOWN_SECTOR_MAPPINGS[tbl.table_name] ||
      "Rural Development";

    const matchesSector =
      selectedSector === "All" || sector === selectedSector;

    const term = searchTerm.toLowerCase();
    const matchesSearch =
      tbl.table_name.toLowerCase().includes(term) ||
      (tbl.description && tbl.description.toLowerCase().includes(term));

    return matchesSector && matchesSearch;
  });

  return (
    <div
      className="fixed inset-0 z-50 overflow-hidden"
      aria-labelledby="drawer-title"
      role="dialog"
      aria-modal="true"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md md:max-w-xl bg-white shadow-2xl flex flex-col">
          {/* Drawer Header */}
          <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
            <div className="flex items-center gap-2.5">
              <Database className="w-5 h-5 text-ashoka-800" />
              <div>
                <h2
                  id="drawer-title"
                  className="text-base font-bold text-slate-900"
                >
                  NDAP Relational Catalogs
                </h2>
                <p className="text-xs text-slate-500">
                  {tables.length} Official Government Databases Registered
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
              aria-label="Close Database Explorer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Search & Sector Filters */}
          <div className="p-4 border-b border-slate-200 space-y-3">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                placeholder="Search datasets, tables, schemes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-ashoka-800/30 focus:border-ashoka-800"
              />
            </div>

            {/* Sector Tabs */}
            <div className="flex flex-wrap gap-1.5">
              {SECTORS.map((sector) => (
                <button
                  key={sector}
                  onClick={() => setSelectedSector(sector)}
                  className={`px-2.5 py-1 text-xs font-medium rounded-full transition-colors ${
                    selectedSector === sector
                      ? "bg-ashoka-900 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {sector}
                </button>
              ))}
            </div>
          </div>

          {/* Drawer Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {isLoading ? (
              <div className="text-center py-12 text-sm text-slate-500">
                <Database className="w-8 h-8 animate-pulse text-ashoka-800 mx-auto mb-2 opacity-50" />
                Loading registered catalogs...
              </div>
            ) : filteredTables.length === 0 ? (
              <div className="text-center py-12 text-sm text-slate-500">
                No datasets matched your filter.
              </div>
            ) : (
              filteredTables.map((tbl) => {
                const isExpanded = expandedTable === tbl.table_name;
                const columns = Array.isArray(tbl.columns)
                  ? tbl.columns
                  : tbl.columns
                  ? Object.entries(tbl.columns).map(([name, type]) => ({
                      name,
                      type: String(type),
                    }))
                  : [];

                return (
                  <div
                    key={tbl.table_name}
                    className="border border-slate-200 rounded-lg p-3 hover:border-slate-300 transition-colors bg-white"
                  >
                    <div
                      className="flex items-start justify-between cursor-pointer"
                      onClick={() =>
                        setExpandedTable(isExpanded ? null : tbl.table_name)
                      }
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-sm text-slate-900 font-mono">
                            {tbl.table_name}
                          </span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 font-medium border border-emerald-200">
                            Parquet Mounted
                          </span>
                        </div>
                        {tbl.description && (
                          <p className="text-xs text-slate-600">
                            {tbl.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 text-xs text-slate-500 pt-1">
                          {tbl.domain && (
                            <span className="inline-flex items-center gap-1">
                              <Layers className="w-3 h-3 text-slate-400" />
                              {tbl.domain}
                            </span>
                          )}
                          {tbl.row_count !== undefined && (
                            <span>{tbl.row_count.toLocaleString()} rows</span>
                          )}
                          {columns.length > 0 && (
                            <span>{columns.length} columns</span>
                          )}
                        </div>
                      </div>
                      <ChevronRight
                        className={`w-4 h-4 text-slate-400 transform transition-transform ${
                          isExpanded ? "rotate-90" : ""
                        }`}
                      />
                    </div>

                    {/* Expanded Columns Table */}
                    {isExpanded && columns.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-100">
                        <p className="text-xs font-semibold text-slate-700 mb-2">
                          Schema Columns:
                        </p>
                        <div className="max-h-48 overflow-y-auto rounded border border-slate-100 divide-y divide-slate-100 text-xs">
                          {columns.map((col, cIdx) => (
                            <div
                              key={cIdx}
                              className="px-2.5 py-1.5 flex items-center justify-between font-mono bg-slate-50/50"
                            >
                              <span className="text-slate-800 font-medium">
                                {col.name}
                              </span>
                              <span className="text-slate-500 text-[11px]">
                                {col.type}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

