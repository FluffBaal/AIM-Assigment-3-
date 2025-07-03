# RAG Chat Application API Documentation

## Base URL

- Development: `http://localhost:8000`
- Production: `https://aim-assigment-3.vercel.app/api`

## Authentication

Most endpoints require an OpenAI API key to be provided in the `X-API-Key` header.

```http
X-API-Key: sk-your-openai-api-key
```

## Endpoints

### Health Check

#### GET /health

Check if the API is running.

**Response**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example**
```bash
curl http://localhost:8000/health
```

---

### Readiness Check

#### GET /ready

Check if the API is ready to handle requests.

**Response**
```json
{
  "status": "ready",
  "checks": {
    "api": true,
    "upload_dir": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example**
```bash
curl http://localhost:8000/ready
```

---

### Upload PDF

#### POST /upload

Upload a PDF file for processing and indexing.

**Headers**
- `X-API-Key`: Your OpenAI API key (required)
- `Content-Type`: multipart/form-data

**Request Body**
- `file`: PDF file (required, max 10MB)

**Response**
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "size": 1048576,
  "pages": 10,
  "chunks": 25,
  "processing_time": 2.5
}
```

**Error Responses**
- `400 Bad Request`: Invalid file format or size
- `401 Unauthorized`: Missing or invalid API key
- `413 Payload Too Large`: File exceeds 10MB limit
- `500 Internal Server Error`: Processing error

**Example**
```bash
curl -X POST http://localhost:8000/upload \
  -H "X-API-Key: sk-your-api-key" \
  -F "file=@document.pdf"
```

---

### Get File Status

#### GET /files/{file_id}

Get the status and metadata of an uploaded file.

**Headers**
- `X-API-Key`: Your OpenAI API key (required)

**Path Parameters**
- `file_id`: UUID of the uploaded file

**Response**
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "status": "processed",
  "uploaded_at": "2024-01-15T10:25:00Z",
  "size": 1048576,
  "pages": 10,
  "chunks": 25,
  "vector_count": 25
}
```

**Error Responses**
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: File not found

**Example**
```bash
curl http://localhost:8000/files/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: sk-your-api-key"
```

---

### Chat with PDF

#### POST /chat

Send a message to chat with an uploaded PDF document.

**Headers**
- `X-API-Key`: Your OpenAI API key (required)
- `Content-Type`: application/json

**Request Body**
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "What is the main topic of this document?",
  "history": [
    {
      "role": "user",
      "content": "Previous question"
    },
    {
      "role": "assistant",
      "content": "Previous answer"
    }
  ]
}
```

**Response (Non-streaming)**
```json
{
  "response": "The main topic of this document is...",
  "sources": [
    {
      "page": 1,
      "text": "Relevant excerpt from the document...",
      "relevance_score": 0.92
    }
  ]
}
```

**Response (Streaming)**
When `Accept: text/event-stream` header is included, the response is streamed as Server-Sent Events:

```
event: content
data: {"type": "content", "content": "The main topic"}

event: content
data: {"type": "content", "content": " of this document is..."}

event: sources
data: {"type": "sources", "sources": [{"page": 1, "text": "...", "relevance_score": 0.92}]}

event: done
data: {"type": "done"}
```

**Error Responses**
- `400 Bad Request`: Invalid request body
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: File not found
- `500 Internal Server Error`: Processing error

**Example (Non-streaming)**
```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "What is this document about?"
  }'
```

**Example (Streaming)**
```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: sk-your-api-key" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "What is this document about?"
  }'
```

---

## Data Types

### ChatMessage
```typescript
interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: ChatSource[];
}
```

### ChatSource
```typescript
interface ChatSource {
  page: number;
  text: string;
  relevance_score: number;
  chunk_id?: string;
}
```

### FileStatus
```typescript
interface FileStatus {
  file_id: string;
  filename: string;
  status: 'uploading' | 'processing' | 'processed' | 'error';
  uploaded_at: string;
  size: number;
  pages: number;
  chunks: number;
  vector_count: number;
  error?: string;
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Error message",
  "type": "error_type",
  "status_code": 400
}
```

Common error types:
- `validation_error`: Invalid request data
- `authentication_error`: Invalid or missing API key
- `not_found`: Resource not found
- `rate_limit_error`: Too many requests
- `processing_error`: Internal processing error

---

## Rate Limiting

The API implements rate limiting to prevent abuse:
- 100 requests per minute per API key
- 10 concurrent file uploads per API key
- 50MB total upload size per hour per API key

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## Webhooks (Future)

Webhook support for async notifications is planned for future releases.

---

## SDK Examples

### Python
```python
import requests

class RAGChatClient:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    def upload_pdf(self, file_path: str) -> dict:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/upload",
                headers=self.headers,
                files=files
            )
            response.raise_for_status()
            return response.json()
    
    def chat(self, file_id: str, message: str, history: list = None) -> dict:
        response = requests.post(
            f"{self.base_url}/chat",
            headers={**self.headers, "Content-Type": "application/json"},
            json={
                "file_id": file_id,
                "message": message,
                "history": history or []
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
client = RAGChatClient("sk-your-api-key")
upload = client.upload_pdf("document.pdf")
response = client.chat(upload["file_id"], "What is this about?")
print(response["response"])
```

### JavaScript/TypeScript
```typescript
class RAGChatClient {
  constructor(
    private apiKey: string,
    private baseUrl: string = 'http://localhost:8000'
  ) {}

  async uploadPDF(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/upload`, {
      method: 'POST',
      headers: { 'X-API-Key': this.apiKey },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async chat(
    fileId: string,
    message: string,
    history: ChatMessage[] = []
  ): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ file_id: fileId, message, history }),
    });

    if (!response.ok) {
      throw new Error(`Chat failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Streaming chat
  streamChat(
    fileId: string,
    message: string,
    onEvent: (event: StreamEvent) => void,
    history: ChatMessage[] = []
  ): () => void {
    const controller = new AbortController();

    fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({ file_id: fileId, message, history }),
      signal: controller.signal,
    })
      .then(response => {
        const reader = response.body!.getReader();
        const decoder = new TextDecoder();

        const readStream = async () => {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                onEvent(data);
              }
            }
          }
        };

        readStream();
      })
      .catch(console.error);

    return () => controller.abort();
  }
}

// Usage
const client = new RAGChatClient('sk-your-api-key');
const file = new File(['content'], 'document.pdf');
const upload = await client.uploadPDF(file);
const response = await client.chat(upload.file_id, 'What is this about?');
console.log(response.response);
```

---

## Best Practices

1. **API Key Security**
   - Never expose API keys in client-side code
   - Use environment variables for API keys
   - Rotate keys regularly

2. **Error Handling**
   - Always check response status codes
   - Implement retry logic for transient errors
   - Log errors for debugging

3. **Performance**
   - Use streaming for better user experience
   - Implement client-side caching where appropriate
   - Batch requests when possible

4. **File Management**
   - Validate file types and sizes before upload
   - Implement progress indicators for uploads
   - Clean up temporary files after processing