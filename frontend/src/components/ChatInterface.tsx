import React, { useState, useRef, useEffect } from 'react';
import { useApiKey } from '../hooks/useApiKey';
import { apiClient } from '../services/api';
import { ChatMessage, ChatSource } from '../types/api';
import { MessageList } from './MessageList';
import { SourcesList } from './SourcesList';

interface ChatInterfaceProps {
  fileId: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ fileId }) => {
  const { apiKey } = useApiKey();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentSources, setCurrentSources] = useState<ChatSource[]>([]);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortStreamRef = useRef<(() => void) | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || !apiKey || isStreaming) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: input.trim(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setError(null);
    setIsStreaming(true);
    setCurrentSources([]);

    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: '',
      sources: [],
    };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      // Use streaming API
      abortStreamRef.current = apiClient.streamChat(
        {
          file_id: fileId,
          message: userMessage.content,
          history: messages,
        },
        apiKey,
        (event) => {
          if (event.type === 'content') {
            setMessages(prev => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage.role === 'assistant') {
                lastMessage.content += event.content || '';
              }
              return newMessages;
            });
          } else if (event.type === 'sources') {
            setCurrentSources(event.sources || []);
            setMessages(prev => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage.role === 'assistant') {
                lastMessage.sources = event.sources;
              }
              return newMessages;
            });
          } else if (event.type === 'error') {
            setError(event.content || 'An error occurred');
          }
        },
        (error) => {
          setError(error.message);
          setIsStreaming(false);
        },
        () => {
          setIsStreaming(false);
        }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      setIsStreaming(false);
    }
  };

  const handleStopStreaming = () => {
    if (abortStreamRef.current) {
      abortStreamRef.current();
      abortStreamRef.current = null;
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-16rem)] gap-6">
      <div className="flex-1 flex flex-col bg-white rounded-lg shadow-sm">
        <div className="flex-1 overflow-y-auto p-4">
          <MessageList messages={messages} />
          <div ref={messagesEndRef} />
        </div>

        {error && (
          <div className="px-4 py-2 bg-red-50 border-t border-red-200">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-4 border-t">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your PDF..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={isStreaming}
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={handleStopStreaming}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                Stop
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim() || !apiKey}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Send
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="w-80 bg-white rounded-lg shadow-sm p-4 overflow-y-auto">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Sources</h3>
        {currentSources.length > 0 ? (
          <SourcesList sources={currentSources} />
        ) : (
          <p className="text-sm text-gray-500">
            Sources will appear here when you ask a question
          </p>
        )}
      </div>
    </div>
  );
};