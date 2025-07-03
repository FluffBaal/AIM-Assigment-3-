// API Response Types

export interface UploadResponse {
  file_id: string;
  filename: string;
  size_bytes: number;
  page_count: number;
  chunk_count: number;
  message: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
}

export interface ChatSource {
  page: number;
  chunk_id: string;
  content: string;
  relevance_score: number;
}

export interface ChatRequest {
  file_id: string;
  message: string;
  history?: ChatMessage[];
}

export interface ChatResponse {
  message: string;
  sources: ChatSource[];
  tokens_used?: number;
}

export interface FileStatus {
  file_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  status: string;
  has_vector_store: boolean;
}

export interface HealthStatus {
  status: string;
  service?: string;
}

export interface ReadinessCheck {
  database: boolean;
  openai: boolean;
  storage: boolean;
}

export interface ErrorResponse {
  error: {
    message: string;
    type: string;
    status_code?: number;
    details?: unknown;
  };
}

// Stream Event Types for SSE
export interface StreamEvent {
  type: 'content' | 'sources' | 'error';
  content?: string;
  sources?: ChatSource[];
}