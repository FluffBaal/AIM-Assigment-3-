import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../../test/test-utils';
import { ChatInterface } from '../ChatInterface';
import { apiClient } from '../../services/api';
import type { StreamEvent } from '../../types/api';

// Mock the API client
vi.mock('../../services/api', () => ({
  apiClient: {
    streamChat: vi.fn(),
    getFileStatus: vi.fn(),
  },
}));

// Mock the useApiKey hook
vi.mock('../../hooks/useApiKey', () => ({
  useApiKey: () => ({ apiKey: 'sk-test-key' }),
}));

describe('ChatInterface', () => {
  const mockFileId = 'test-file-123';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders chat interface', () => {
    render(<ChatInterface fileId={mockFileId} />);
    
    expect(screen.getByPlaceholderText('Ask a question about your PDF...')).toBeInTheDocument();
    expect(screen.getByText('Send')).toBeInTheDocument();
    expect(screen.getByText('Sources')).toBeInTheDocument();
  });

  it('handles message submission', async () => {
    const mockStreamChat = vi.fn();
    (apiClient.streamChat as any).mockImplementation(mockStreamChat);

    render(<ChatInterface fileId={mockFileId} />);
    
    const input = screen.getByPlaceholderText('Ask a question about your PDF...');
    const sendButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'What is this document about?' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(mockStreamChat).toHaveBeenCalledWith(
        {
          file_id: mockFileId,
          message: 'What is this document about?',
          history: [],
        },
        'sk-test-key',
        expect.any(Function),
        expect.any(Function),
        expect.any(Function)
      );
    });
    
    // Input should be cleared
    expect(input).toHaveValue('');
  });

  it('displays user and assistant messages', async () => {
    render(<ChatInterface fileId={mockFileId} />);
    
    const input = screen.getByPlaceholderText('Ask a question about your PDF...');
    const sendButton = screen.getByText('Send');
    
    // Submit a message
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(sendButton);
    
    // Check user message appears
    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument();
    });
  });

  it('handles streaming responses', async () => {
    let streamCallback: (event: StreamEvent) => void = () => {};
    
    (apiClient.streamChat as any).mockImplementation(
      (request: any, apiKey: string, onEvent: (event: StreamEvent) => void) => {
        streamCallback = onEvent;
        return () => {}; // abort function
      }
    );

    render(<ChatInterface fileId={mockFileId} />);
    
    const input = screen.getByPlaceholderText('Ask a question about your PDF...');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(screen.getByText('Send'));
    
    await waitFor(() => {
      expect(screen.getByText('Test message')).toBeInTheDocument();
    });
    
    // Simulate streaming content
    streamCallback({ type: 'content', content: 'This is ' });
    streamCallback({ type: 'content', content: 'a streaming ' });
    streamCallback({ type: 'content', content: 'response.' });
    
    await waitFor(() => {
      expect(screen.getByText('This is a streaming response.')).toBeInTheDocument();
    });
  });

  it('displays sources when provided', async () => {
    let streamCallback: (event: StreamEvent) => void = () => {};
    
    (apiClient.streamChat as any).mockImplementation(
      (request: any, apiKey: string, onEvent: (event: StreamEvent) => void) => {
        streamCallback = onEvent;
        return () => {};
      }
    );

    render(<ChatInterface fileId={mockFileId} />);
    
    const input = screen.getByPlaceholderText('Ask a question about your PDF...');
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.click(screen.getByText('Send'));
    
    // Simulate sources
    streamCallback({
      type: 'sources',
      sources: [
        { page: 1, text: 'Source text 1', relevance_score: 0.9 },
        { page: 2, text: 'Source text 2', relevance_score: 0.8 },
      ],
    });
    
    await waitFor(() => {
      expect(screen.getByText('Page 1')).toBeInTheDocument();
      expect(screen.getByText('Source text 1')).toBeInTheDocument();
      expect(screen.getByText('Page 2')).toBeInTheDocument();
      expect(screen.getByText('Source text 2')).toBeInTheDocument();
    });
  });

  it('shows loading state during streaming', async () => {
    (apiClient.streamChat as any).mockImplementation(() => () => {});

    render(<ChatInterface fileId={mockFileId} />);
    
    const input = screen.getByPlaceholderText('Ask a question about your PDF...');
    const sendButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.click(sendButton);
    
    // Should show stop button instead of send
    await waitFor(() => {
      expect(screen.getByText('Stop')).toBeInTheDocument();
      expect(screen.queryByText('Send')).not.toBeInTheDocument();
    });
    
    // Input should be disabled
    expect(input).toBeDisabled();
  });

  it('handles stop streaming', async () => {
    const mockAbort = vi.fn();
    (apiClient.streamChat as any).mockImplementation(() => mockAbort);

    render(<ChatInterface fileId={mockFileId} />);
    
    const input = screen.getByPlaceholderText('Ask a question about your PDF...');
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.click(screen.getByText('Send'));
    
    await waitFor(() => {
      expect(screen.getByText('Stop')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Stop'));
    
    expect(mockAbort).toHaveBeenCalled();
    
    await waitFor(() => {
      expect(screen.getByText('Send')).toBeInTheDocument();
    });
  });

  it('handles errors during streaming', async () => {
    let errorCallback: (error: Error) => void = () => {};
    
    (apiClient.streamChat as any).mockImplementation(
      (request: any, apiKey: string, onEvent: any, onError: (error: Error) => void) => {
        errorCallback = onError;
        return () => {};
      }
    );

    render(<ChatInterface fileId={mockFileId} />);
    
    const input = screen.getByPlaceholderText('Ask a question about your PDF...');
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.click(screen.getByText('Send'));
    
    // Simulate error
    errorCallback(new Error('Connection failed'));
    
    await waitFor(() => {
      expect(screen.getByText('Connection failed')).toBeInTheDocument();
    });
  });

  it('prevents submission without input', () => {
    render(<ChatInterface fileId={mockFileId} />);
    
    const sendButton = screen.getByText('Send');
    fireEvent.click(sendButton);
    
    expect(apiClient.streamChat).not.toHaveBeenCalled();
  });

  it('prevents submission without API key', () => {
    // Mock no API key
    vi.mock('../../hooks/useApiKey', () => ({
      useApiKey: () => ({ apiKey: null }),
    }));
    
    render(<ChatInterface fileId={mockFileId} />);
    
    const sendButton = screen.getByText('Send');
    expect(sendButton).toBeDisabled();
  });

  it('handles Enter key submission', async () => {
    const mockStreamChat = vi.fn();
    (apiClient.streamChat as any).mockImplementation(mockStreamChat);

    render(<ChatInterface fileId={mockFileId} />);
    
    const input = screen.getByPlaceholderText('Ask a question about your PDF...');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    await waitFor(() => {
      expect(mockStreamChat).toHaveBeenCalled();
    });
  });

  it('maintains message history', async () => {
    let streamCallback: (event: StreamEvent) => void = () => {};
    
    (apiClient.streamChat as any).mockImplementation(
      (request: any, apiKey: string, onEvent: (event: StreamEvent) => void) => {
        streamCallback = onEvent;
        return () => {};
      }
    );

    render(<ChatInterface fileId={mockFileId} />);
    
    // First message
    const input = screen.getByPlaceholderText('Ask a question about your PDF...');
    fireEvent.change(input, { target: { value: 'First question' } });
    fireEvent.click(screen.getByText('Send'));
    
    streamCallback({ type: 'content', content: 'First answer' });
    streamCallback({ type: 'done' });
    
    await waitFor(() => {
      expect(screen.getByText('First question')).toBeInTheDocument();
      expect(screen.getByText('First answer')).toBeInTheDocument();
    });
    
    // Second message - should include history
    fireEvent.change(input, { target: { value: 'Second question' } });
    fireEvent.click(screen.getByText('Send'));
    
    await waitFor(() => {
      expect(apiClient.streamChat).toHaveBeenLastCalledWith(
        expect.objectContaining({
          message: 'Second question',
          history: expect.arrayContaining([
            expect.objectContaining({ role: 'user', content: 'First question' }),
            expect.objectContaining({ role: 'assistant', content: 'First answer' }),
          ]),
        }),
        expect.any(String),
        expect.any(Function),
        expect.any(Function),
        expect.any(Function)
      );
    });
  });
});