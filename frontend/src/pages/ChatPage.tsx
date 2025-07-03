import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChatInterface } from '../components/ChatInterface';
import { useApiKey } from '../hooks/useApiKey';
import { apiClient } from '../services/api';

export const ChatPage: React.FC = () => {
  const { fileId } = useParams<{ fileId: string }>();
  const navigate = useNavigate();
  const { apiKey } = useApiKey();
  const [fileName, setFileName] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!apiKey) {
      navigate('/');
      return;
    }

    if (!fileId) {
      navigate('/');
      return;
    }

    // Fetch file status
    const fetchFileStatus = async () => {
      try {
        const status = await apiClient.getFileStatus(fileId, apiKey);
        setFileName(status.filename);
      } catch (error) {
        console.error('Failed to fetch file status:', error);
        navigate('/');
      } finally {
        setIsLoading(false);
      }
    };

    fetchFileStatus();
  }, [fileId, apiKey, navigate]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="h-full">
      <div className="mb-6">
        <button
          onClick={() => navigate('/')}
          className="text-sm text-gray-600 hover:text-gray-900 mb-2"
        >
          ← Back to upload
        </button>
        <h2 className="text-2xl font-bold text-gray-900">
          Chat with: {fileName}
        </h2>
      </div>
      
      {fileId && <ChatInterface fileId={fileId} />}
    </div>
  );
};