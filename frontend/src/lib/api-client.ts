import {
  BackendHealthResponse,
  QueryResponse,
  SchemasResponse,
  VoiceTranscribeResponse,
} from "@/types/api";

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
).replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (error: unknown) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError("Could not connect to the IndicSQL backend.", 0);
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload &&
      typeof payload.detail === "string"
        ? payload.detail
        : `Request failed with status ${response.status}.`;
    throw new ApiError(detail, response.status);
  }

  return payload as T;
}

export const apiClient = {
  checkHealth(): Promise<BackendHealthResponse> {
    return request("/health");
  },

  fetchSchemas(): Promise<SchemasResponse> {
    return request("/schemas");
  },

  submitQuery(query: string, signal?: AbortSignal): Promise<QueryResponse> {
    return request("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
      signal,
    });
  },

  transcribeAudio(audio: Blob): Promise<VoiceTranscribeResponse> {
    const body = new FormData();
    body.append("file", audio, "recording.webm");
    return request("/voice/transcribe", { method: "POST", body });
  },
};
