"use client";

import React, { useState } from "react";
import { Database, Menu, X, BookOpen, Github } from "lucide-react";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { Button } from "@/components/ui/Button";

interface HeaderProps {
  backendStatus: "connected" | "disconnected" | "checking";
  tableCount?: number;
  onOpenExplorer: () => void;
}

export function Header({
  backendStatus,
  tableCount,
  onOpenExplorer,
}: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Product Brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-ashoka-900 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              🇮🇳
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-xl tracking-tight text-ashoka-950">
                  BharatQuery
                </span>
                <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-ashoka-100 text-ashoka-800 rounded">
                  IndicSQL
                </span>
              </div>
              <p className="hidden sm:block text-xs text-slate-500 font-medium">
                Public Data. Your Language. Clear Answers.
              </p>
            </div>
          </div>

          {/* Desktop Navigation & Actions */}
          <div className="hidden md:flex items-center gap-4">
            <StatusIndicator status={backendStatus} tableCount={tableCount} />

            <Button
              variant="outline"
              size="sm"
              onClick={onOpenExplorer}
              className="border-slate-300 text-slate-700 hover:bg-slate-50"
            >
              <Database className="w-4 h-4 text-ashoka-800" />
              <span>Explore Databases</span>
            </Button>

            <a
              href="https://github.com/ojhaprathmesh/IndicSQL_Repo"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub Repository"
              className="text-slate-500 hover:text-slate-800 transition-colors p-1.5"
            >
              <Github className="w-5 h-5" />
            </a>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center gap-2">
            <StatusIndicator status={backendStatus} />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden py-3 border-t border-slate-200 space-y-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setMobileMenuOpen(false);
                onOpenExplorer();
              }}
              className="w-full justify-start"
            >
              <Database className="w-4 h-4 text-ashoka-800" />
              <span>Explore 20 NDAP Databases</span>
            </Button>
            <a
              href="https://github.com/ojhaprathmesh/IndicSQL_Repo"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 rounded-md"
            >
              <Github className="w-4 h-4" />
              <span>GitHub Repository</span>
            </a>
          </div>
        )}
      </div>
    </header>
  );
}

