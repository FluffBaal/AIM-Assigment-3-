/**
 * API Factory to select between regular and stateless API based on environment
 */
import { apiClient } from './api';
import { statelessApiClient } from './statelessApi';

// Check if we're in a Vercel environment
const isVercel = import.meta.env.VITE_VERCEL === 'true' || 
                 window.location.hostname.includes('vercel.app') ||
                 window.location.hostname.includes('vercel.sh');

// Export the appropriate client based on environment
export const api = isVercel ? statelessApiClient : apiClient;

// Type exports for convenience
export type { ProcessedPDF, StatelessChatRequest, StreamEvent } from './statelessApi';
export type { 
  UploadResponse, 
  ChatRequest, 
  ChatResponse, 
  FileStatus, 
  ChatMessage, 
  ChatSource 
} from '../types/api';