from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Dict
import json
import logging
import asyncio

from backend.app.api.dependencies import get_api_key
from backend.app.models.chat import ChatRequest, ChatResponse
from backend.app.services.chat_service import ChatService
from backend.app.middleware.rate_limiter import api_key_limiter, RATE_LIMITS

logger = logging.getLogger(__name__)
router = APIRouter()

chat_service = ChatService()

@router.post("/message")
@api_key_limiter.limit(RATE_LIMITS["chat"])
async def chat_message(
    req: Request,
    request: ChatRequest,
    api_key: str = Depends(get_api_key)
) -> ChatResponse:
    try:
        # Get response from chat service
        response = await chat_service.generate_response(
            file_id=request.file_id,
            message=request.message,
            history=request.history,
            api_key=api_key
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate response")

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Stream endpoint called with message: {request.message[:50]}...")
    
    async def generate() -> AsyncGenerator[str, None]:
        try:
            # Stream directly without collecting chunks first
            has_sent_content = False
            
            async for chunk in chat_service.generate_stream(
                file_id=request.file_id,
                message=request.message,
                history=request.history,
                api_key=api_key
            ):
                logger.info(f"Streaming chunk: type={chunk.get('type')}, content_length={len(chunk.get('content', ''))}")
                
                # Format as Server-Sent Events
                data = json.dumps({
                    "type": chunk["type"],
                    "content": chunk.get("content", ""),
                    "sources": chunk.get("sources", [])
                })
                yield f"data: {data}\n\n"
                
                if chunk.get("type") == "content":
                    has_sent_content = True
                
                # Flush to ensure data is sent immediately
                await asyncio.sleep(0)  # Allow other tasks to run
            
            if not has_sent_content:
                logger.error("No content chunks were sent")
                # Add a fallback message
                error_data = json.dumps({
                    "type": "content", 
                    "content": "I apologize, but I'm having trouble generating a response. Please try again."
                })
                yield f"data: {error_data}\n\n"
        
        except Exception as e:
            logger.error(f"Stream error: {type(e).__name__}: {str(e)}", exc_info=True)
            error_data = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {error_data}\n\n"
        finally:
            logger.info("Sending [DONE] signal")
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
            "Transfer-Encoding": "chunked",
        }
    )

@router.delete("/history/{file_id}")
async def clear_chat_history(
    file_id: str,
    api_key: str = Depends(get_api_key)
) -> Dict[str, str]:
    success = chat_service.clear_history(file_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"message": "Chat history cleared successfully"}