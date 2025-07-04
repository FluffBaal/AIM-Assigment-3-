# Simple Vercel Deployment for Temporary Chat Sessions

## Architecture Overview

Since you only need to store files temporarily for the duration of a chat session, we can use a much simpler approach:

### 1. **Vercel's /tmp Directory**
- Serverless functions have access to a `/tmp` directory
- Files persist for the duration of the function instance (not guaranteed between requests)
- Limited to 512MB total

### 2. **In-Memory Storage for Vectors**
- Store vectors and metadata in memory during the chat session
- Use the PDF file directly from `/tmp` when needed

### 3. **Session-Based Architecture**
- Each upload creates a temporary session
- Files and vectors exist only during the active chat
- No persistence needed between sessions

## Implementation Strategy

### Option 1: Stateless with Embedded Vectors in Response
```python
# When uploading:
1. Save PDF to /tmp temporarily
2. Process and create embeddings
3. Return embeddings with the upload response
4. Frontend stores embeddings in memory

# When chatting:
1. Frontend sends query + embeddings
2. Backend performs similarity search
3. Returns response
```

### Option 2: Edge Runtime with Temporary Storage
```python
# Use Vercel Edge Functions
1. Store PDF in memory as base64
2. Process on-demand
3. Keep in Edge Function memory cache
```

### Option 3: URL-Based Processing
```python
# Process PDFs from URLs
1. User uploads PDF to a temporary file service (like file.io)
2. Backend fetches and processes PDF from URL
3. No storage needed on Vercel
```

## Recommended Approach: Client-Side Storage

For the simplest implementation:

1. **Upload PDF** → Process in backend → Return vectors to frontend
2. **Store vectors** in browser's IndexedDB or memory
3. **Send vectors** with each chat request
4. **No server-side storage** needed

This approach:
- ✅ Works within Vercel's limits
- ✅ No storage costs
- ✅ Simple implementation
- ✅ Scales automatically
- ❌ Larger request payloads
- ❌ Re-upload needed for new sessions