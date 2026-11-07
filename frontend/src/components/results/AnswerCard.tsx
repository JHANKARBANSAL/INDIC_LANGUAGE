"use client";

import React, { useState } from "react";
import { Volume2, VolumeX, Copy, Check, Sparkles, Database } from "lucide-react";
import { QueryResponse } from "@/types/api";
import { playTextToSpeech } from "@/lib/speech";

interface AnswerCardProps {
  data: QueryResponse;
}

export function AnswerCard({ data }: AnswerCardProps) {
  const [copied, setCopied] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [stopAudioFn, setStopAudioFn] = useState<(() => void) | null>(null);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(data.verbalized_response);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  };

  const handleToggleAudio = async () => {
    if (isPlayingAudio && stopAudioFn) {
      stopAudioFn();
      setIsPlayingAudio(false);
      setStopAudioFn(null);
      return;
    }

    setIsPlayingAudio(true);
    const stopFn = await playTextToSpeech(
      data.verbalized_response,
      data.detected_language,
      () => {
        setIsPlayingAudio(false);
        setStopAudioFn(null);
      },
      () => {
        setIsPlayingAudio(false);
        setStopAudioFn(null);
      }
    );
    setStopAudioFn(() => stopFn);
  };

  // Find linked table from audit trace if present
  const schemaStep = data.audit_trace?.find(
    (step) => step.agent === "SchemaLinkerAgent" || step.action === "cross_lingual_lookup"
  );
  const linkedTable = schemaStep?.matched_table;

  return (
    <div className="bg-gradient-to-b from-white to-slate-50/60 border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
      {/* Header Info Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-ashoka-100 text-ashoka-900 border border-ashoka-200">
            <Sparkles className="w-3.5 h-3.5 text-ashoka-700" />
            <span>Answer ({data.detected_language?.toUpperCase() || "INDIC"})</span>
          </span>
          {data.detected_script && (
            <span className="text-xs text-slate-500 font-medium">
              Script: {data.detected_script}
            </span>
          )}
        </div>

        {linkedTable && (
          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono bg-slate-100 text-slate-700 border border-slate-200">
            <Database className="w-3.5 h-3.5 text-ashoka-800" />
            <span>{linkedTable}</span>
          </div>
        )}
      </div>

      {/* Main Mother-Tongue Prose Answer */}
      <div className="text-slate-900 font-medium text-lg sm:text-xl leading-relaxed">
        {data.verbalized_response || "No answer generated for this query."}
      </div>

      {/* Action Controls */}
      <div className="flex items-center justify-end gap-2 pt-2">
        {/* Text-to-speech speaker button */}
        <button
          type="button"
          onClick={handleToggleAudio}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
            isPlayingAudio
              ? "bg-ashoka-900 text-white border-ashoka-900 animate-pulse"
              : "bg-white hover:bg-slate-50 text-slate-700 border-slate-300"
          }`}
          title={isPlayingAudio ? "Stop Audio" : "Listen in Mother Tongue"}
          aria-label={isPlayingAudio ? "Stop Audio Playback" : "Play Vernacular Audio"}
        >
          {isPlayingAudio ? (
            <>
              <VolumeX className="w-4 h-4 text-emerald-400" />
              <span>Stop Speaking</span>
            </>
          ) : (
            <>
              <Volume2 className="w-4 h-4 text-ashoka-800" />
              <span>Read Aloud</span>
            </>
          )}
        </button>

        {/* Copy answer */}
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 transition-colors"
          title="Copy Answer text"
        >
          {copied ? (
            <>
              <Check className="w-4 h-4 text-emerald-600" />
              <span className="text-emerald-700 font-semibold">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-4 h-4" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}

