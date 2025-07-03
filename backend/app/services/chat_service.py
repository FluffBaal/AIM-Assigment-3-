import os
import logging
from typing import List, Dict, Any, AsyncGenerator

from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.openai_utils.prompts import SystemRolePrompt, UserRolePrompt
from app.models.chat import ChatMessage, ChatResponse, ChatSource
from app.services.pdf_service import PDFService
from app.core.config import settings

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided PDF document context.
Always cite your sources by mentioning which parts of the document support your answer.
If the answer cannot be found in the provided context, say so clearly.
Be concise but thorough in your responses."""

class ChatService:
    def __init__(self):
        self.pdf_service = PDFService()
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
        search_results = vector_store.search(message, k=5)
        
        # Prepare context
        context_chunks = []
        sources = []
        
        for idx, (chunk_text, metadata, score) in enumerate(search_results):
            context_chunks.append(f"[Source {idx + 1}] {chunk_text}")
            sources.append(ChatSource(
                page=metadata["page"],
                chunk_id=metadata["chunk_id"],
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
        chat_model = ChatOpenAI(model=settings.chat_model)
        
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
        search_results = vector_store.search(message, k=5)
        
        # Prepare context and sources
        context_chunks = []
        sources = []
        
        for idx, (chunk_text, metadata, score) in enumerate(search_results):
            context_chunks.append(f"[Source {idx + 1}] {chunk_text}")
            sources.append({
                "page": metadata["page"],
                "chunk_id": metadata["chunk_id"],
                "content": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text,
                "relevance_score": float(score)
            })
        
        # Yield sources first
        yield {"type": "sources", "sources": sources}
        
        context = "\n\n".join(context_chunks)
        
        # Prepare messages
        messages = [
            SystemRolePrompt(RAG_SYSTEM_PROMPT).create_message(),
            UserRolePrompt(f"Context from PDF:\n{context}\n\nUser Question: {message}").create_message()
        ]
        
        # Set API key and create chat model
        os.environ["OPENAI_API_KEY"] = api_key
        chat_model = ChatOpenAI(model=settings.chat_model)
        
        # Stream response
        full_response = ""
        async for chunk in chat_model.stream(messages):
            if chunk:
                full_response += chunk
                yield {"type": "content", "content": chunk}
        
        # Store in history
        if file_id not in self.chat_histories:
            self.chat_histories[file_id] = []
        
        self.chat_histories[file_id].append(ChatMessage(role="user", content=message))
        self.chat_histories[file_id].append(ChatMessage(role="assistant", content=full_response, sources=sources))
    
    def clear_history(self, file_id: str) -> bool:
        if file_id in self.chat_histories:
            self.chat_histories[file_id] = []
            return True
        return False
    
    def get_history(self, file_id: str) -> List[ChatMessage]:
        return self.chat_histories.get(file_id, [])