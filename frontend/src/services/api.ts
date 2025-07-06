import axios from 'axios';
import type { AxiosInstance } from 'axios';
import type {
  UploadResponse,
  ChatRequest,
  ChatResponse,
  FileStatus,
  HealthStatus,
  ReadinessCheck,
  StreamEvent
} from '../types/api';

class ApiClient {
  private axios: AxiosInstance;

  constructor() {
    this.axios = axios.create({
      baseURL: '/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.data?.error) {
          throw new Error(error.response.data.error.message);
        }
        throw error;
      }
    );
  }

  private getAuthHeaders(apiKey: string) {
    return {
      'X-API-Key': apiKey,
    };
  }

  // Health endpoints
  async checkHealth(): Promise<HealthStatus> {
    const response = await this.axios.get<HealthStatus>('/health/status');
    return response.data;
  }

  async checkReadiness(): Promise<ReadinessCheck> {
    const response = await this.axios.get<ReadinessCheck>('/health/ready');
    return response.data;
  }

  // Upload endpoints
  async uploadPDF(file: File, apiKey: string): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.axios.post<UploadResponse>(
      '/upload/pdf',
      formData,
      {
        headers: {
          ...this.getAuthHeaders(apiKey),
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  async getFileStatus(fileId: string, apiKey: string): Promise<FileStatus> {
    const response = await this.axios.get<FileStatus>(
      `/upload/pdf/${fileId}/status`,
      {
        headers: this.getAuthHeaders(apiKey),
      }
    );
    return response.data;
  }

  // Chat endpoints
  async sendMessage(request: ChatRequest, apiKey: string): Promise<ChatResponse> {
    const response = await this.axios.post<ChatResponse>(
      '/chat/message',
      request,
      {
        headers: this.getAuthHeaders(apiKey),
      }
    );
    return response.data;
  }

  streamChat(
    request: ChatRequest,
    apiKey: string,
    onMessage: (event: StreamEvent) => void,
    onError: (error: Error) => void,
    onComplete: () => void
  ): () => void {
    // Use fetch with ReadableStream for SSE since EventSource doesn't support POST
    const abortController = new AbortController();
    
    
    fetch('/api/v1/chat/stream', {
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
            let buffer = '';
            
            while (true) {
              const { done, value } = await reader.read();
              
              if (done) {
                onComplete();
                break;
              }
              
              const chunk = decoder.decode(value, { stream: true });
              buffer += chunk;
              
              // Process complete lines
              const lines = buffer.split('\n');
              buffer = lines.pop() || ''; // Keep incomplete line in buffer
              
              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  const data = line.slice(6).trim();
                  
                  if (data === '[DONE]') {
                    onComplete();
                    return;
                  }
                  
                  if (data) {
                    try {
                      const event = JSON.parse(data) as StreamEvent;
                      onMessage(event);
                    } catch (e) {
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
    
    // Return abort function
    return () => {
      abortController.abort();
    };
  }

  async clearChatHistory(fileId: string, apiKey: string): Promise<void> {
    await this.axios.delete(`/chat/history/${fileId}`, {
      headers: this.getAuthHeaders(apiKey),
    });
  }
}

export const apiClient = new ApiClient();