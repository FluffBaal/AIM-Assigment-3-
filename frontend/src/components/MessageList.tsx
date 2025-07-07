import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessage } from '../types/api';

interface MessageListProps {
  messages: ChatMessage[];
}

export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="space-y-4">
      {messages.map((message, index) => (
        <div
          key={index}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[80%] px-4 py-2 rounded-lg ${
              message.role === 'user'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-900'
            }`}
          >
            {message.role === 'user' ? (
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={{
                    // Custom components for better research paper rendering
                    h1: ({node, ...props}) => <h1 className="text-lg font-bold mt-2 mb-1" {...props} />,
                    h2: ({node, ...props}) => <h2 className="text-base font-bold mt-2 mb-1" {...props} />,
                    h3: ({node, ...props}) => <h3 className="text-sm font-bold mt-1 mb-1" {...props} />,
                    p: ({node, ...props}) => <p className="mb-2 text-sm" {...props} />,
                    ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2" {...props} />,
                    ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-2" {...props} />,
                    li: ({node, ...props}) => <li className="mb-1 text-sm" {...props} />,
                    code: ({node, inline, ...props}) => 
                      inline ? (
                        <code className="bg-gray-200 px-1 rounded text-xs" {...props} />
                      ) : (
                        <code className="block bg-gray-200 p-2 rounded text-xs overflow-x-auto" {...props} />
                      ),
                    blockquote: ({node, ...props}) => (
                      <blockquote className="border-l-4 border-gray-300 pl-3 italic my-2 text-sm" {...props} />
                    ),
                    strong: ({node, ...props}) => <strong className="font-semibold" {...props} />,
                    em: ({node, ...props}) => <em className="italic" {...props} />,
                    a: ({node, ...props}) => (
                      <a className="text-indigo-600 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />
                    ),
                    table: ({node, ...props}) => (
                      <table className="border-collapse border border-gray-300 my-2" {...props} />
                    ),
                    th: ({node, ...props}) => (
                      <th className="border border-gray-300 px-2 py-1 bg-gray-100 text-sm font-semibold" {...props} />
                    ),
                    td: ({node, ...props}) => (
                      <td className="border border-gray-300 px-2 py-1 text-sm" {...props} />
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
            {message.sources && message.sources.length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-300">
                <p className="text-xs opacity-75">
                  Based on {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
                </p>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};