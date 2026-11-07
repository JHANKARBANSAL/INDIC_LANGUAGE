/**
 * Strongly-typed API Contracts for BharatQuery / IndicSQL Backend.
 */

export interface ExecutionResult {
  columns: string[];
  rows: (string | number | boolean | null)[][];
  row_count?: number;
  execution_time_ms?: number;
}

export interface AuditStep {
  step: number;
  agent: string;
  action: string;
  matched_table?: string;
  matched_columns?: string[];
  confidence?: number;
  [key: string]: unknown;
}

export interface QueryResponse {
  query_id: string;
  raw_query: string;
  detected_language: string;
  detected_script: string;
  generated_sql: string;
  verbalized_response: string;
  execution_result: ExecutionResult | null;
  audit_trace?: AuditStep[];
}

export interface QueryRequest {
  query: string;
  session_id?: string;
}

export interface BackendHealthResponse {
  status: string;
}

export interface RootServiceResponse {
  service: string;
  version: string;
  status: string;
  supported_languages: string[];
}

export interface VoiceTranscribeResponse {
  transcript: string;
  detected_language: string;
  raw_response?: Record<string, unknown>;
}

export interface VoiceSynthesizeRequest {
  text: string;
  language_code?: string;
  speaker?: string;
}

export interface VoiceSynthesizeResponse {
  audio_base64?: string;
  target_language_code?: string;
  speaker?: string;
}

export interface ColumnMetadata {
  name: string;
  type: string;
  nullable?: boolean;
  description?: string;
}

export interface TableMetadata {
  table_name: string;
  domain?: string;
  description?: string;
  row_count?: number;
  columns?: ColumnMetadata[] | Record<string, string>;
}

export interface SchemasResponse {
  count: number;
  tables: Record<string, TableMetadata>;
}

