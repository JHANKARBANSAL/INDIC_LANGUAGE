"use client";

import React from "react";
import { Sparkles } from "lucide-react";

interface SampleQuestionsProps {
  onSelectQuestion: (query: string) => void;
  disabled?: boolean;
}

const SAMPLE_CHIPS = [
  {
    lang: "Marathi",
    query: "महाराष्ट्रात पीएम-किसानचे लाभार्थी किती आहेत?",
    icon: "🌾",
  },
  {
    lang: "Hindi",
    query: "बिहार में महिला साक्षरता दर कितनी है?",
    icon: "📚",
  },
  {
    lang: "Hinglish",
    query: "UP mein urea fertilizer sales kitni hui?",
    icon: "🚜",
  },
  {
    lang: "Tamil",
    query: "தமிழ்நாட்டில் ஊரக சாலை வளர்ச்சி எப்படி உள்ளது?",
    icon: "🛣️",
  },
  {
    lang: "Telugu",
    query: "ఆంధ్రప్రదేశ్లో జల్ జీవన్ మిషన్ కనెక్షన్లు ఎన్ని?",
    icon: "💧",
  },
];

export function SampleQuestions({
  onSelectQuestion,
  disabled = false,
}: SampleQuestionsProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500">
        <Sparkles className="w-3.5 h-3.5 text-ashoka-700" />
        <span>Try asking a sample question across languages:</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {SAMPLE_CHIPS.map((chip, idx) => (
          <button
            key={idx}
            type="button"
            disabled={disabled}
            onClick={() => onSelectQuestion(chip.query)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full bg-slate-100/80 hover:bg-slate-200/80 text-slate-700 border border-slate-200 transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed group focus:outline-none focus:ring-2 focus:ring-ashoka-800/20"
          >
            <span>{chip.icon}</span>
            <span className="font-semibold text-ashoka-900">[{chip.lang}]:</span>
            <span className="text-slate-600 group-hover:text-slate-900">
              {chip.query}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

