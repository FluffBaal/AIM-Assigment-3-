"""
Stateless API endpoints for Vercel deployment
All data is returned to client, no server storage
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, AsyncGenerator
from pydantic import BaseModel
import json
import logging

from app.api.dependencies import get_api_key
from app.services.pdf_service_stateless import stateless_pdf_service
from app.services.chat_service_stateless import stateless_chat_service
from app.models.chat import ChatMessage
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class ProcessedPDFResponse(BaseModel):
    file_id: str
    filename: str
    page_count: int
    chunk_count: int
    chunks: List[str]
    embeddings: List[List[float]]
    chunk_metadata: List[Dict[str, Any]]
    message: str

class StatelessChatRequest(BaseModel):
    message: str
    chunks: List[str]
    embeddings: List[List[float]]
    chunk_metadata: List[Dict[str, Any]]
    history: List[ChatMessage] = []

@router.post("/upload/process", response_model=ProcessedPDFResponse)
async def process_pdf_stateless(
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key)
):
    """
    Process PDF and return all data to client.
    Client stores this data for the chat session.
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Check file size
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    
    if file_size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=413, 
            detail=f"File size exceeds maximum allowed size of {settings.max_upload_size_mb}MB"
        )
    
    try:
        # Process PDF and return all data
        result = await stateless_pdf_service.process_pdf_and_return_data(
            file_content=contents,
            filename=file.filename,
            api_key=api_key
        )
        
        logger.info(f"Successfully processed PDF: {result['file_id']}")
        return ProcessedPDFResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to process PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process PDF")

@router.post("/chat/stateless")
async def chat_stateless(
    request: StatelessChatRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Chat endpoint that receives all context data from client.
    No server-side storage needed.
    """
    try:
        response = await stateless_chat_service.generate_response_with_context(
            message=request.message,
            chunks=request.chunks,
            embeddings=request.embeddings,
            chunk_metadata=request.chunk_metadata,
            api_key=api_key,
            history=request.history
        )
        return response
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stateless/stream")
async def chat_stateless_stream(
    request: StatelessChatRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Streaming chat endpoint that receives all context data from client.
    """
    async def generate() -> AsyncGenerator[str, None]:
        try:
            async for chunk in stateless_chat_service.generate_stream_with_context(
                message=request.message,
                chunks=request.chunks,
                embeddings=request.embeddings,
                chunk_metadata=request.chunk_metadata,
                api_key=api_key,
                history=request.history
            ):
                data = json.dumps(chunk)
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            error_data = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {error_data}\n\n"
        finally:
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )