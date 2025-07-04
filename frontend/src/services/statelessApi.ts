/**
 * Stateless API client for Vercel deployment
 * Stores PDF data in browser memory/IndexedDB
 */

import axios, { AxiosInstance } from 'axios';
import type { ChatMessage, ChatSource } from '../types/api';

export interface ProcessedPDF {
  file_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  chunks: string[];
  embeddings: number[][];
  chunk_metadata: Array<{
    page: number;
    chunk_index: number;
    total_chunks: number;
  }>;
}

export interface StatelessChatRequest {
  message: string;
  chunks: string[];
  embeddings: number[][];
  chunk_metadata: Array<{
    page: number;
    chunk_index: number;
    total_chunks: number;
  }>;
  history?: ChatMessage[];
}

export interface StreamEvent {
  type: 'content' | 'sources' | 'error';
  content?: string;
  sources?: ChatSource[];
}

class StatelessAPIClient {
  private axios: AxiosInstance;
  private storedPDFData: Map<string, ProcessedPDF> = new Map();

  constructor(baseURL: string = '/api/v1') {
    this.axios = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Try to restore from sessionStorage
    this.restoreFromSession();
  }

  private getAuthHeaders(apiKey: string) {
    return {
      'X-API-Key': apiKey,
    };
  }

  private saveToSession() {
    // Store in sessionStorage for page refreshes
    const data = Array.from(this.storedPDFData.entries());
    sessionStorage.setItem('pdf_data', JSON.stringify(data));
  }

  private restoreFromSession() {
    const stored = sessionStorage.getItem('pdf_data');
    if (stored) {
      try {
        const data = JSON.parse(stored);
        this.storedPDFData = new Map(data);
      } catch (e) {
        console.error('Failed to restore PDF data:', e);
      }
    }
  }

  async uploadAndProcessPDF(file: File, apiKey: string): Promise<ProcessedPDF> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.axios.post<ProcessedPDF>(
      '/stateless/upload/process',
      formData,
      {
        headers: {
          ...this.getAuthHeaders(apiKey),
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    // Store the processed data
    this.storedPDFData.set(response.data.file_id, response.data);
    this.saveToSession();

    return response.data;
  }

  getPDFData(fileId: string): ProcessedPDF | undefined {
    return this.storedPDFData.get(fileId);
  }

  async sendMessage(
    fileId: string,
    message: string,
    history: ChatMessage[],
    apiKey: string
  ) {
    const pdfData = this.storedPDFData.get(fileId);
    if (!pdfData) {
      throw new Error('PDF data not found. Please re-upload the PDF.');
    }

    const request: StatelessChatRequest = {
      message,
      chunks: pdfData.chunks,
      embeddings: pdfData.embeddings,
      chunk_metadata: pdfData.chunk_metadata,
      history,
    };

    const response = await this.axios.post(
      '/stateless/chat/stateless',
      request,
      {
        headers: this.getAuthHeaders(apiKey),
      }
    );

    return response.data;
  }

  streamChat(
    fileId: string,
    message: string,
    history: ChatMessage[],
    apiKey: string,
    onMessage: (event: StreamEvent) => void,
    onError: (error: Error) => void,
    onComplete: () => void
  ): () => void {
    const pdfData = this.storedPDFData.get(fileId);
    if (!pdfData) {
      onError(new Error('PDF data not found. Please re-upload the PDF.'));
      return () => {};
    }

    const abortController = new AbortController();
    
    const request: StatelessChatRequest = {
      message,
      chunks: pdfData.chunks,
      embeddings: pdfData.embeddings,
      chunk_metadata: pdfData.chunk_metadata,
      history,
    };

    fetch('/api/v1/stateless/chat/stateless/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify(request),
      signal: abortController.signal,
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        
        if (!reader) {
          throw new Error('No response body');
        }

        const readStream = async () => {
          try {
            while (true) {
              const { done, value } = await reader.read();
              
              if (done) {
                onComplete();
                break;
              }
              
              const chunk = decoder.decode(value, { stream: true });
              const lines = chunk.split('\n');
              
              for (const line of lines) {
                const trimmedLine = line.trim();
                if (trimmedLine.startsWith('data: ')) {
                  const data = trimmedLine.slice(6);
                  
                  if (data === '[DONE]') {
                    onComplete();
                    return;
                  }
                  
                  if (data) {
                    try {
                      const event = JSON.parse(data) as StreamEvent;
                      onMessage(event);
                    } catch (e) {
                      console.error('Failed to parse event:', e);
                    }
                  }
                }
              }
            }
          } catch (error) {
            if (!abortController.signal.aborted) {
              onError(error as Error);
            }
          }
        };
        
        readStream();
      })
      .catch(error => {
        if (!abortController.signal.aborted) {
          onError(error);
        }
      });
    
    return () => abortController.abort();
  }

  clearStoredData() {
    this.storedPDFData.clear();
    sessionStorage.removeItem('pdf_data');
  }
}

export const statelessApiClient = new StatelessAPIClient();