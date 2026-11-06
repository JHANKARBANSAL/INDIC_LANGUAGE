"use client";

import React, { useRef, useState } from "react";
import { Mic, MicOff, Loader2, AlertCircle } from "lucide-react";
import { AudioRecorder, isAudioRecordingSupported } from "@/lib/speech";
import { apiClient } from "@/lib/api-client";

interface VoiceInputProps {
  onTranscriptReady: (transcript: string) => void;
  disabled?: boolean;
}

type VoiceState =
  | "idle"
  | "requesting_permission"
  | "recording"
  | "transcribing"
  | "permission_denied"
  | "unsupported"
  | "failed";

export function VoiceInput({
  onTranscriptReady,
  disabled = false,
}: VoiceInputProps) {
  const [state, setState] = useState<VoiceState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const recorderRef = useRef<AudioRecorder | null>(null);

  const startRecording = async () => {
    setErrorMessage(null);
    if (!isAudioRecordingSupported()) {
      setState("unsupported");
      setErrorMessage("Audio recording is not supported in this browser.");
      return;
    }

    try {
      setState("requesting_permission");
      const recorder = new AudioRecorder();
      recorderRef.current = recorder;
      await recorder.start();
      setState("recording");
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "NotAllowedError") {
        setState("permission_denied");
        setErrorMessage("Microphone permission was denied.");
      } else {
        setState("failed");
        setErrorMessage(
          err instanceof Error ? err.message : "Failed to access microphone."
        );
      }
    }
  };

  const stopRecording = async () => {
    if (!recorderRef.current || state !== "recording") return;

    try {
      setState("transcribing");
      const audioBlob = await recorderRef.current.stop();

      // Attempt backend Sarvam Speech-to-Text transcription with auto language detection
      try {
        const res = await apiClient.transcribeAudio(audioBlob);
        if (res.transcript && res.transcript.trim()) {
          onTranscriptReady(res.transcript.trim());
          setState("idle");
          return;
        }
      } catch (backendErr: unknown) {
        // Fallback: If backend is unconfigured or returns error, inform user
        const detail =
          backendErr instanceof Error
            ? backendErr.message
            : "Backend transcription unavailable";
        setErrorMessage(`Transcription: ${detail}`);
      }

      setState("idle");
    } catch (err: unknown) {
      setState("failed");
      setErrorMessage(
        err instanceof Error ? err.message : "Failed to process audio recording."
      );
      if (recorderRef.current) {
        recorderRef.current.cleanup();
      }
    }
  };

  const isRecording = state === "recording";
  const isTranscribing = state === "transcribing";

  return (
    <div className="relative inline-flex items-center">
      {isRecording ? (
        <button
          type="button"
          onClick={stopRecording}
          disabled={disabled}
          title="Click to stop recording"
          aria-label="Stop Voice Recording"
          className="relative inline-flex items-center justify-center p-2.5 rounded-xl bg-red-500 hover:bg-red-600 text-white transition-all shadow-md focus:outline-none focus:ring-2 focus:ring-red-400"
        >
          {/* Pulsing recording ring */}
          <span className="absolute -inset-1 rounded-xl bg-red-400 opacity-75 animate-ping" />
          <MicOff className="w-5 h-5 relative z-10" />
        </button>
      ) : (
        <button
          type="button"
          onClick={startRecording}
          disabled={disabled || isTranscribing}
          title="Click and speak in any Indian language (Hindi, Marathi, Bengali, Tamil, Telugu, English)"
          aria-label="Start Voice Recording"
          className="p-2.5 rounded-xl text-slate-500 hover:text-ashoka-900 hover:bg-slate-100 transition-colors disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-ashoka-800/30"
        >
          {isTranscribing ? (
            <Loader2 className="w-5 h-5 animate-spin text-ashoka-800" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
        </button>
      )}

      {/* Floating Status / Error Tooltip */}
      {errorMessage && (
        <div className="absolute bottom-full right-0 mb-2 w-64 p-2 text-xs bg-red-50 text-red-800 border border-red-200 rounded-lg shadow-lg flex items-start gap-1.5 z-30">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span>{errorMessage}</span>
            <button
              onClick={() => setErrorMessage(null)}
              className="ml-1 underline font-semibold text-red-900"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Recording State Pill */}
      {isRecording && (
        <div className="absolute right-full mr-3 whitespace-nowrap px-2.5 py-1 rounded-md bg-red-50 border border-red-200 text-red-700 text-xs font-medium flex items-center gap-1.5 shadow-sm animate-pulse">
          <span className="w-2 h-2 rounded-full bg-red-600" />
          Listening (Speak in any language)...
        </div>
      )}
      {isTranscribing && (
        <div className="absolute right-full mr-3 whitespace-nowrap px-2.5 py-1 rounded-md bg-ashoka-50 border border-ashoka-200 text-ashoka-800 text-xs font-medium flex items-center gap-1.5 shadow-sm">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-ashoka-800" />
          Detecting language & transcribing...
        </div>
      )}
    </div>
  );
}

