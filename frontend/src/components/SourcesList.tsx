import React from 'react';
import type { ChatSource } from '../types/api';

interface SourcesListProps {
  sources: ChatSource[];
}

export const SourcesList: React.FC<SourcesListProps> = ({ sources }) => {
  return (
    <div className="space-y-3">
      {sources.map((source, index) => (
        <div
          key={source.chunk_id}
          className="p-3 bg-gray-50 rounded-lg border border-gray-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-600">
              Source {index + 1}
            </span>
            <span className="text-xs text-gray-500">
              Page {source.page}
            </span>
          </div>
          <p className="text-sm text-gray-700 line-clamp-3">
            {source.content}
          </p>
          <div className="mt-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Relevance</span>
              <span className="text-xs font-medium text-gray-600">
                {(source.relevance_score * 100).toFixed(1)}%
              </span>
            </div>
            <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5">
              <div
                className="bg-indigo-600 h-1.5 rounded-full"
                style={{ width: `${source.relevance_score * 100}%` }}
              ></div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};