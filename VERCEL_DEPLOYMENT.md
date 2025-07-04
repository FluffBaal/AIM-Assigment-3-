# Vercel Deployment Architecture for RAG Application

## Storage Solutions

### 1. Vercel Blob for PDF Files
- Store uploaded PDFs in Vercel Blob storage
- Supports files up to 5TB with multipart uploads
- Returns unique, unguessable URLs for each file
- Built on AWS S3 with 99.999999999% reliability

### 2. Vercel KV for Metadata & Vector Storage
- Use Vercel KV (serverless Redis) for:
  - File metadata (filename, upload date, etc.)
  - Vector embeddings (serialized)
  - Chat histories
  - Session data

### 3. Vercel Postgres (Optional)
- For more complex queries and relationships
- Store user data, file ownership, etc.

## Implementation Changes Needed

### Backend Changes

1. **Install Vercel Storage SDKs**
```bash
npm install @vercel/blob @vercel/kv
```

2. **Update PDF Upload Service**
```python
# Instead of local file storage
from vercel import blob

async def upload_pdf_to_blob(file_content: bytes, filename: str):
    # Upload to Vercel Blob
    blob_url = await blob.put(filename, file_content)
    return blob_url
```

3. **Update Vector Storage**
```python
from vercel import kv
import json

async def store_vectors(file_id: str, vectors: list):
    # Serialize vectors and store in KV
    await kv.set(f"vectors:{file_id}", json.dumps(vectors))
    
async def get_vectors(file_id: str):
    # Retrieve and deserialize vectors
    data = await kv.get(f"vectors:{file_id}")
    return json.loads(data) if data else None
```

### Frontend Changes

1. **Client-side Upload for Large Files**
```typescript
// For files > 4.5MB, use client upload
import { upload } from '@vercel/blob/client';

const blob = await upload(filename, file, {
  access: 'public',
  handleUploadUrl: '/api/upload-url',
});
```

## Environment Variables

Add these to your Vercel project:
```
BLOB_READ_WRITE_TOKEN=your_blob_token
KV_URL=your_kv_url
KV_REST_API_URL=your_kv_rest_url
KV_REST_API_TOKEN=your_kv_token
KV_REST_API_READ_ONLY_TOKEN=your_kv_read_token
```

## Serverless Function Considerations

1. **4.5MB Request Limit**: Use client uploads for PDFs > 4.5MB
2. **Execution Time**: Max 5 minutes for hobby, 15 minutes for pro
3. **Memory**: 1024MB default, can increase to 3008MB

## Cost Optimization

1. **Vercel Blob**: $0.15/GB stored + $0.36/GB bandwidth
2. **Vercel KV**: Free tier includes 30k requests/month
3. **Use caching** to minimize repeated embedding generation

## Migration Steps

1. Set up Vercel Blob and KV in your project dashboard
2. Update backend to use Vercel storage instead of local files
3. Implement client-side uploads for large PDFs
4. Store vectors and metadata in KV
5. Update retrieval logic to fetch from cloud storage