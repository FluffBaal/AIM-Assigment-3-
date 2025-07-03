# Deployment Guide for RAG Chat Application

This guide covers deploying the RAG Chat Application to Vercel.

## Prerequisites

- Vercel account (free tier works)
- GitHub repository connected to Vercel
- OpenAI API key for testing

## Deployment Architecture

The application is deployed as:
- **Frontend**: Static React app served by Vercel's CDN
- **Backend**: Python serverless functions using Vercel's Python runtime

## Step-by-Step Deployment

### 1. Fork or Clone Repository

```bash
git clone https://github.com/FluffBaal/AIM-Assigment-3-.git
cd AIM-Assigment-3-
```

### 2. Install Vercel CLI (Optional)

```bash
npm install -g vercel
```

### 3. Connect to Vercel

#### Option A: Using Vercel Dashboard
1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Vercel will auto-detect the configuration

#### Option B: Using CLI
```bash
vercel
```

### 4. Configure Environment Variables

In Vercel Dashboard, go to Settings → Environment Variables and add:

```
UPLOAD_DIR=/tmp/uploads
```

Note: The OpenAI API key is provided by users in the frontend, not stored on the server.

### 5. Deploy

#### Automatic Deployment
- Push to main branch triggers automatic deployment
- Pull requests create preview deployments

#### Manual Deployment
```bash
vercel --prod
```

## Configuration Files

### vercel.json
Already configured in the repository:
- Frontend build command
- Python serverless functions
- Routing rules
- File upload directory

### requirements.txt
Python dependencies for serverless functions are automatically installed.

## Production Considerations

### 1. CORS Configuration
Update `backend/app/core/config.py` to include your production domain:

```python
cors_origins: List[str] = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://your-app.vercel.app",
    "https://your-custom-domain.com"
]
```

### 2. File Upload Limitations
- Vercel serverless functions have a 10MB payload limit
- Files are stored temporarily in `/tmp` (512MB limit)
- Consider using external storage (S3, Cloudinary) for production

### 3. Function Timeout
- Current timeout: 60 seconds
- Sufficient for most PDF processing
- Can be increased with Vercel Pro plan

### 4. Cold Starts
- First request may be slower due to cold start
- Subsequent requests are faster
- Consider warming strategies for production

## Monitoring

### Vercel Dashboard
- Real-time logs
- Function metrics
- Error tracking

### Custom Monitoring
Consider adding:
- Sentry for error tracking
- Analytics for usage metrics
- Custom logging for debugging

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure all dependencies are in requirements.txt
   - Check Python version compatibility (3.11)

2. **CORS errors**
   - Add production domain to CORS origins
   - Verify API endpoint URLs

3. **File upload failures**
   - Check file size limits
   - Verify `/tmp` directory permissions

4. **Function timeouts**
   - Optimize PDF processing
   - Consider chunking large operations

### Debug Steps

1. Check Vercel function logs:
   ```bash
   vercel logs
   ```

2. Test locally with Vercel CLI:
   ```bash
   vercel dev
   ```

3. Verify environment variables are set correctly

## Security Best Practices

1. **API Keys**
   - Never commit API keys to repository
   - Users provide their own OpenAI keys
   - Keys are stored in browser localStorage only

2. **File Validation**
   - PDF files are validated before processing
   - File size limits enforced
   - Malicious file checks implemented

3. **Rate Limiting**
   - Consider implementing rate limiting for production
   - Use Vercel Edge Middleware for protection

4. **HTTPS**
   - Automatically enabled on Vercel
   - Enforced for all API calls

## Scaling Considerations

### Current Architecture Limitations
- In-memory vector storage (resets on function cold start)
- Single-region deployment
- No persistent storage

### Production Scaling Options
1. **Vector Database**: Migrate to Pinecone, Weaviate, or Qdrant
2. **File Storage**: Use S3 or Cloudinary
3. **Caching**: Implement Redis for session management
4. **Multi-region**: Use Vercel Edge Functions

## Cost Estimation

### Vercel Free Tier Includes:
- 100GB bandwidth
- 100GB-hours serverless function execution
- Unlimited static requests

### Estimated Costs for Small-Medium Usage:
- Free tier usually sufficient for <1000 users/month
- Pro plan ($20/month) for increased limits
- Enterprise for custom requirements

## Support

For deployment issues:
1. Check [Vercel Documentation](https://vercel.com/docs)
2. Review [GitHub Issues](https://github.com/FluffBaal/AIM-Assigment-3-/issues)
3. Contact Vercel support for platform-specific issues