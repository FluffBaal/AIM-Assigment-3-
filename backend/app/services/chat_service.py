import os
import logging
from typing import List, Dict, Any, AsyncGenerator

from backend.aimakerspace.openai_utils.chatmodel import ChatOpenAI
from backend.aimakerspace.openai_utils.prompts import SystemRolePrompt, UserRolePrompt
from backend.app.models.chat import ChatMessage, ChatResponse, ChatSource
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided PDF document context.
Always cite your sources by mentioning which parts of the document support your answer.
If the answer cannot be found in the provided context, say so clearly.
Be concise but thorough in your responses."""

class ChatService:
    def __init__(self):
        # Import here to avoid circular imports
        from backend.app.services import pdf_service_instance
        self.pdf_service = pdf_service_instance
        self.chat_histories: Dict[str, List[ChatMessage]] = {}
    
    async def generate_response(
        self,
        file_id: str,
        message: str,
        history: List[ChatMessage],
        api_key: str
    ) -> ChatResponse:
        # Get vector store
        vector_store = self.pdf_service.get_vector_store(file_id)
        if not vector_store:
            raise ValueError(f"No indexed document found for file_id: {file_id}")
        
        # Search for relevant chunks
        search_results = vector_store.search_by_text(message, k=5)
        
        # Prepare context
        context_chunks = []
        sources = []
        
        # Get metadata stored in vector_store
        metadata_list = getattr(vector_store, 'metadata', [])
        
        for idx, (chunk_text, score) in enumerate(search_results):
            context_chunks.append(f"[Source {idx + 1}] {chunk_text}")
            # Find matching metadata by chunk text
            chunk_metadata = {}
            for i, chunk in enumerate(vector_store.vectors.keys()):
                if chunk == chunk_text and i < len(metadata_list):
                    chunk_metadata = metadata_list[i]
                    break
            
            sources.append(ChatSource(
                page=chunk_metadata.get("page", 1),
                chunk_id=chunk_metadata.get("chunk_id", f"chunk_{idx}"),
                content=chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text,
                relevance_score=float(score)
            ))
        
        context = "\n\n".join(context_chunks)
        
        # Prepare messages
        messages = [
            SystemRolePrompt(RAG_SYSTEM_PROMPT).create_message(),
            UserRolePrompt(f"Context from PDF:\n{context}\n\nUser Question: {message}").create_message()
        ]
        
        # Add history if provided
        for hist_msg in history[-5:]:  # Limit history to last 5 messages
            if hist_msg.role == "user":
                messages.append(UserRolePrompt(hist_msg.content).create_message())
            else:
                messages.append({"role": "assistant", "content": hist_msg.content})
        
        # Set API key and create chat model
        os.environ["OPENAI_API_KEY"] = api_key
        chat_model = ChatOpenAI(model_name=settings.chat_model)
        
        # Generate response
        response = chat_model.run(messages)
        
        # Store in history
        if file_id not in self.chat_histories:
            self.chat_histories[file_id] = []
        
        self.chat_histories[file_id].append(ChatMessage(role="user", content=message))
        self.chat_histories[file_id].append(ChatMessage(role="assistant", content=response, sources=[s.dict() for s in sources]))
        
        return ChatResponse(
            message=response,
            sources=sources
        )
    
    async def generate_stream(
        self,
        file_id: str,
        message: str,
        history: List[ChatMessage],
        api_key: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        # Get vector store
        vector_store = self.pdf_service.get_vector_store(file_id)
        if not vector_store:
            raise ValueError(f"No indexed document found for file_id: {file_id}")
        
        # Search for relevant chunks
        search_results = vector_store.search_by_text(message, k=5)
        
        # Prepare context and sources
        context_chunks = []
        sources = []
        
        # Get metadata stored in vector_store
        metadata_list = getattr(vector_store, 'metadata', [])
        
        for idx, (chunk_text, score) in enumerate(search_results):
            context_chunks.append(f"[Source {idx + 1}] {chunk_text}")
            # Find matching metadata by chunk text
            chunk_metadata = {}
            for i, chunk in enumerate(vector_store.vectors.keys()):
                if chunk == chunk_text and i < len(metadata_list):
                    chunk_metadata = metadata_list[i]
                    break
            
            sources.append({
                "page": chunk_metadata.get("page", 1),
                "chunk_id": chunk_metadata.get("chunk_id", f"chunk_{idx}"),
                "content": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text,
                "relevance_score": float(score)
            })
        
        # Yield sources first
        yield {"type": "sources", "sources": sources}
        logger.info("Sources yielded, preparing to call OpenAI")
        
        
        context = "\n\n".join(context_chunks)
        
        # Prepare messages
        messages = [
            SystemRolePrompt(RAG_SYSTEM_PROMPT).create_message(),
            UserRolePrompt(f"Context from PDF:\n{context}\n\nUser Question: {message}").create_message()
        ]
        
        # Set API key and create chat model
        os.environ["OPENAI_API_KEY"] = api_key
        logger.info(f"API key set: {api_key[:20]}...")
        
        chat_model = ChatOpenAI(model_name=settings.chat_model)
        
        # Stream response
        full_response = ""
        logger.info(f"Starting stream with model: {settings.chat_model}")
        logger.info(f"Messages count: {len(messages)}")
        logger.info(f"First message preview: {str(messages[0])[:200]}...")
        
        try:
            stream = chat_model.astream(messages)
            logger.info(f"Stream created: {type(stream)}")
            
            chunk_count = 0
            async for chunk in stream:
                chunk_count += 1
                logger.info(f"Received chunk {chunk_count}: {repr(chunk)[:100]}")
                if chunk:
                    full_response += chunk
                    yield {"type": "content", "content": chunk}
                    logger.info(f"Yielded content chunk: {repr(chunk)[:50]}")
            
            logger.info(f"Stream completed. Total chunks: {chunk_count}, Full response length: {len(full_response)}")
            
            if chunk_count == 0:
                logger.warning("No chunks received from OpenAI")
                # Try non-streaming as fallback
                logger.info("Attempting non-streaming fallback")
                response = chat_model.run(messages)
                if response:
                    yield {"type": "content", "content": response}
                    full_response = response
                else:
                    yield {"type": "error", "content": "No response received from AI model"}
                
        except Exception as e:
            logger.error(f"Error during streaming: {type(e).__name__}: {str(e)}", exc_info=True)
            # Try non-streaming as fallback
            try:
                logger.info("Attempting non-streaming fallback after error")
                response = chat_model.run(messages)
                if response:
                    yield {"type": "content", "content": response}
                    full_response = response
                else:
                    yield {"type": "error", "content": f"Streaming error: {str(e)}"}
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {str(fallback_error)}")
                yield {"type": "error", "content": f"Both streaming and fallback failed: {str(e)}"}
        
        # Store in history
        if file_id not in self.chat_histories:
            self.chat_histories[file_id] = []
        
        self.chat_histories[file_id].append(ChatMessage(role="user", content=message))
        self.chat_histories[file_id].append(ChatMessage(role="assistant", content=full_response, sources=sources))
        
        logger.info("generate_stream method completed")
    
    def clear_history(self, file_id: str) -> bool:
        if file_id in self.chat_histories:
            self.chat_histories[file_id] = []
            return True
        return False
    
    def get_history(self, file_id: str) -> List[ChatMessage]:
        return self.chat_histories.get(file_id, [])