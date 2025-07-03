from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Dict
import json
import logging

from app.api.dependencies import get_api_key
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter()

chat_service = ChatService()

@router.post("/message")
async def chat_message(
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
    async def generate() -> AsyncGenerator[str, None]:
        try:
            async for chunk in chat_service.generate_stream(
                file_id=request.file_id,
                message=request.message,
                history=request.history,
                api_key=api_key
            ):
                # Format as Server-Sent Events
                data = json.dumps({
                    "type": chunk["type"],
                    "content": chunk.get("content", ""),
                    "sources": chunk.get("sources", [])
                })
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

@router.delete("/history/{file_id}")
async def clear_chat_history(
    file_id: str,
    api_key: str = Depends(get_api_key)
) -> Dict[str, str]:
    success = chat_service.clear_history(file_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"message": "Chat history cleared successfully"}