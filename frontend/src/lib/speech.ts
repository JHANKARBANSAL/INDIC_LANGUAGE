export function isAudioRecordingSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof MediaRecorder !== "undefined" &&
    typeof navigator.mediaDevices?.getUserMedia === "function"
  );
}

export class AudioRecorder {
  private recorder: MediaRecorder | null = null;
  private stream: MediaStream | null = null;
  private chunks: BlobPart[] = [];

  async start(): Promise<void> {
    if (!isAudioRecordingSupported()) {
      throw new Error("Audio recording is not supported in this browser.");
    }
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.chunks = [];
    this.recorder = new MediaRecorder(this.stream);
    this.recorder.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) this.chunks.push(event.data);
    });
    this.recorder.start();
  }

  stop(): Promise<Blob> {
    if (!this.recorder || this.recorder.state === "inactive") {
      return Promise.reject(new Error("No active audio recording."));
    }
    const recorder = this.recorder;
    return new Promise((resolve, reject) => {
      recorder.addEventListener(
        "stop",
        () => {
          const blob = new Blob(this.chunks, {
            type: recorder.mimeType || "audio/webm",
          });
          this.cleanup();
          resolve(blob);
        },
        { once: true }
      );
      recorder.addEventListener(
        "error",
        () => {
          this.cleanup();
          reject(new Error("Audio recording failed."));
        },
        { once: true }
      );
      recorder.stop();
    });
  }

  cleanup(): void {
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.recorder = null;
    this.chunks = [];
  }
}

const speechLocales: Record<string, string> = {
  bn: "bn-IN",
  en: "en-IN",
  hi: "hi-IN",
  "hi-en": "hi-IN",
  mr: "mr-IN",
  ta: "ta-IN",
  te: "te-IN",
};

export async function playTextToSpeech(
  text: string,
  language: string,
  onEnd: () => void,
  onError: () => void
): Promise<() => void> {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    onError();
    return () => undefined;
  }

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = speechLocales[language.toLowerCase()] || "en-IN";
  utterance.onend = onEnd;
  utterance.onerror = onError;
  window.speechSynthesis.speak(utterance);

  return () => {
    window.speechSynthesis.cancel();
    onEnd();
  };
}
