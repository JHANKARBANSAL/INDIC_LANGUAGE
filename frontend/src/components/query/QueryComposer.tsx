"use client";

import React, { useRef } from "react";
import { ArrowUp, X, Sparkles } from "lucide-react";
import { VoiceInput } from "@/components/query/VoiceInput";
import { SampleQuestions } from "@/components/query/SampleQuestions";
import { Button } from "@/components/ui/Button";

interface QueryComposerProps {
  query: string;
  onChange: (query: string) => void;
  onSubmit: (query: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function QueryComposer({
  query,
  onChange,
  onSubmit,
  isLoading,
  disabled = false,
}: QueryComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (query.trim() && !isLoading && !disabled) {
        onSubmit(query);
      }
    }
  };

  const handleVoiceTranscript = (transcript: string) => {
    onChange(transcript);
    // Focus textarea after voice transcription
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const handleClear = () => {
    onChange("");
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      {/* Input Box Shell */}
      <div className="relative bg-white border border-slate-300 rounded-2xl shadow-sm hover:border-slate-400 focus-within:border-ashoka-800 focus-within:ring-2 focus-within:ring-ashoka-800/20 transition-all p-3 sm:p-4">
        {/* Multiline textarea */}
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isLoading}
          rows={3}
          placeholder="Ask a question about India's public data in Marathi, Hindi, Tamil, Telugu, Bengali, Hinglish, or English..."
          className="w-full bg-transparent resize-none border-0 text-slate-900 placeholder:text-slate-400 focus:outline-none text-base sm:text-lg leading-relaxed disabled:opacity-50"
        />

        {/* Bottom Actions Row */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100">
          <div className="flex items-center gap-2">
            {query.trim().length > 0 && (
              <button
                type="button"
                onClick={handleClear}
                disabled={isLoading || disabled}
                className="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
                <span>Clear</span>
              </button>
            )}
            <span className="hidden sm:inline-block text-[11px] text-slate-400">
              Press <kbd className="px-1 py-0.5 bg-slate-100 border border-slate-200 rounded text-slate-600 font-mono">Enter ↵</kbd> to ask, <kbd className="px-1 py-0.5 bg-slate-100 border border-slate-200 rounded text-slate-600 font-mono">Shift+Enter</kbd> for new line
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Zero-Dropdown Auto-Detecting Voice Input */}
            <VoiceInput
              onTranscriptReady={handleVoiceTranscript}
              disabled={disabled || isLoading}
            />

            {/* Submit Button */}
            <Button
              type="button"
              onClick={() => query.trim() && onSubmit(query)}
              disabled={!query.trim() || disabled || isLoading}
              isLoading={isLoading}
              size="md"
              className="rounded-xl px-4 py-2 font-semibold shadow"
            >
              <span className="hidden sm:inline">Ask BharatQuery</span>
              <ArrowUp className="w-4 h-4 sm:hidden" />
            </Button>
          </div>
        </div>
      </div>

      {/* Suggested Query Chips */}
      <SampleQuestions
        onSelectQuestion={(q) => {
          onChange(q);
          if (textareaRef.current) textareaRef.current.focus();
        }}
        disabled={isLoading || disabled}
      />
    </div>
  );
}

