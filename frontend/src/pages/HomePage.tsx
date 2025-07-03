import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiKeyModal } from '../components/ApiKeyModal';
import { PDFUpload } from '../components/PDFUpload';
import { useApiKey } from '../hooks/useApiKey';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { apiKey, setApiKey } = useApiKey();
  const [isApiKeyModalOpen, setIsApiKeyModalOpen] = useState(!apiKey);

  const handleApiKeySubmit = (key: string) => {
    setApiKey(key);
    setIsApiKeyModalOpen(false);
  };

  const handleFileUploaded = (fileId: string) => {
    navigate(`/chat/${fileId}`);
  };

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Chat with your PDF documents
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Upload a PDF document and start asking questions. Our RAG system will find
          relevant information and provide accurate answers with source citations.
        </p>
      </div>

      {apiKey ? (
        <div className="max-w-2xl mx-auto">
          <PDFUpload onFileUploaded={handleFileUploaded} />
          
          <div className="mt-4 text-center">
            <button
              onClick={() => setIsApiKeyModalOpen(true)}
              className="text-sm text-gray-500 hover:text-gray-700 underline"
            >
              Change API Key
            </button>
          </div>
        </div>
      ) : (
        <div className="text-center">
          <button
            onClick={() => setIsApiKeyModalOpen(true)}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Get Started
          </button>
        </div>
      )}

      <ApiKeyModal
        isOpen={isApiKeyModalOpen}
        onClose={() => apiKey && setIsApiKeyModalOpen(false)}
        onSubmit={handleApiKeySubmit}
      />
    </div>
  );
};