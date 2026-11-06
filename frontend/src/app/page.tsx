"use client";

import React, { useEffect, useRef, useState } from "react";
import { Header } from "@/components/layout/Header";
import { DatabaseDrawer } from "@/components/layout/DatabaseDrawer";
import { QueryComposer } from "@/components/query/QueryComposer";
import { ResultsWorkspace } from "@/components/results/ResultsWorkspace";
import { apiClient, ApiError } from "@/lib/api-client";
import { QueryResponse, SchemasResponse } from "@/types/api";

export default function Home() {
  const [query, setQuery] = useState("");
  const [resultData, setResultData] = useState<QueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Backend state
  const [backendStatus, setBackendStatus] = useState<
    "connected" | "disconnected" | "checking"
  >("checking");
  const [schemas, setSchemas] = useState<SchemasResponse | null>(null);
  const [isLoadingSchemas, setIsLoadingSchemas] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  // 1. Initial Health and Schema Fetch
  useEffect(() => {
    let isMounted = true;

    async function initBackend() {
      try {
        await apiClient.checkHealth();
        if (!isMounted) return;
        setBackendStatus("connected");

        // Fetch registered schemas
        setIsLoadingSchemas(true);
        const schemaData = await apiClient.fetchSchemas();
        if (isMounted) {
          setSchemas(schemaData);
        }
      } catch {
        if (isMounted) {
          setBackendStatus("disconnected");
        }
      } finally {
        if (isMounted) {
          setIsLoadingSchemas(false);
        }
      }
    }

    initBackend();

    return () => {
      isMounted = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // 2. Query Submission Handler
  const handleQuerySubmit = async (submittedQuery: string) => {
    if (!submittedQuery.trim()) return;

    // Abort previous in-flight request if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.submitQuery(
        submittedQuery,
        controller.signal
      );
      setResultData(response);
      setBackendStatus("connected");
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        return;
      }
      if (err instanceof ApiError) {
        setError(err.message);
        if (err.status === 0) {
          setBackendStatus("disconnected");
        }
      } else {
        setError("An unexpected error occurred while processing your query.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const tableCount = schemas?.count;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Navigation Header */}
      <Header
        backendStatus={backendStatus}
        tableCount={tableCount}
        onOpenExplorer={() => setIsDrawerOpen(true)}
      />

      {/* Main Content Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-8">
        {/* Hero Title */}
        <div className="text-center max-w-3xl mx-auto space-y-2.5">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-ashoka-950 tracking-tight">
            Indian Public Data in Your Mother Tongue
          </h1>
          <p className="text-sm sm:text-base text-slate-600 leading-relaxed max-w-2xl mx-auto">
            Autonomous multi-agent Text-to-SQL swarm for 20 Government of India (NDAP)
            datasets. Ask freely in Hindi, Marathi, Bengali, Tamil, Telugu, Hinglish, or English.
          </p>
        </div>

        {/* Query Input Section */}
        <section aria-label="Query Composer">
          <QueryComposer
            query={query}
            onChange={setQuery}
            onSubmit={handleQuerySubmit}
            isLoading={isLoading}
          />
        </section>

        {/* Results Workspace */}
        <section aria-label="Query Results">
          <ResultsWorkspace
            data={resultData}
            isLoading={isLoading}
            error={error}
          />
        </section>
      </main>

      {/* 20 NDAP Database Slide-Over Explorer */}
      <DatabaseDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        schemas={schemas}
        isLoading={isLoadingSchemas}
      />

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500 space-y-1">
        <p>
          🇮🇳 <strong>BharatQuery</strong> • Built on the IndicDB Benchmark & National Data and Analytics Platform (NDAP).
        </p>
        <p className="text-[11px] text-slate-400">
          Strictly read-only query execution sandbox with zero destructive database mutations.
        </p>
      </footer>
    </div>
  );
}

