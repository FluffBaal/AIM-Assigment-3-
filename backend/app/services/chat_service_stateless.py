"""
Stateless Chat Service for Vercel Deployment
Receives embeddings from client with each request
"""
import os
import logging
from typing import List, Dict, Any, AsyncGenerator
import numpy as np

from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.openai_utils.prompts import SystemRolePrompt, UserRolePrompt
from app.models.chat import ChatMessage, ChatResponse, ChatSource
from app.core.config import settings

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided PDF document context.
Always cite your sources by mentioning which parts of the document support your answer.
If the answer cannot be found in the provided context, say so clearly.
Be concise but thorough in your responses."""

class StatelessChatService:
    """
    Processes chat requests with embeddings provided by client.
    No server-side storage required.
    """
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    async def generate_response_with_context(
        self,
        message: str,
        chunks: List[str],
        embeddings: List[List[float]],
        chunk_metadata: List[Dict[str, Any]],
        api_key: str,
        history: List[ChatMessage] = None
    ) -> ChatResponse:
        """Generate response using provided chunks and embeddings"""
        
        # Get embedding for the query
        os.environ["OPENAI_API_KEY"] = api_key
        from aimakerspace.openai_utils.embedding import EmbeddingModel
        embedding_model = EmbeddingModel(embeddings_model_name=settings.embedding_model)
        query_embedding = await embedding_model.async_get_embedding(message)
        
        # Find most similar chunks
        similarities = []
        for idx, chunk_embedding in enumerate(embeddings):
            similarity = self.cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((idx, similarity))
        
        # Sort by similarity and get top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_k = 5
        
        # Prepare context and sources
        context_chunks = []
        sources = []
        
        for idx, (chunk_idx, score) in enumerate(similarities[:top_k]):
            chunk_text = chunks[chunk_idx]
            chunk_meta = chunk_metadata[chunk_idx] if chunk_idx < len(chunk_metadata) else {}
            
            context_chunks.append(f"[Source {idx + 1}] {chunk_text}")
            sources.append(ChatSource(
                page=chunk_meta.get("page", idx + 1),
                chunk_id=f"chunk_{chunk_idx}",
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
        if history:
            for hist_msg in history[-5:]:  # Limit history
                if hist_msg.role == "user":
                    messages.append(UserRolePrompt(hist_msg.content).create_message())
                else:
                    messages.append({"role": "assistant", "content": hist_msg.content})
        
        # Generate response
        chat_model = ChatOpenAI(model_name=settings.chat_model)
        response = chat_model.run(messages)
        
        return ChatResponse(
            message=response,
            sources=sources
        )
    
    async def generate_stream_with_context(
        self,
        message: str,
        chunks: List[str],
        embeddings: List[List[float]],
        chunk_metadata: List[Dict[str, Any]],
        api_key: str,
        history: List[ChatMessage] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response using provided chunks and embeddings"""
        
        # Get embedding for the query
        os.environ["OPENAI_API_KEY"] = api_key
        from aimakerspace.openai_utils.embedding import EmbeddingModel
        embedding_model = EmbeddingModel(embeddings_model_name=settings.embedding_model)
        query_embedding = await embedding_model.async_get_embedding(message)
        
        # Find most similar chunks
        similarities = []
        for idx, chunk_embedding in enumerate(embeddings):
            similarity = self.cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((idx, similarity))
        
        # Sort by similarity and get top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_k = 5
        
        # Prepare context and sources
        context_chunks = []
        sources = []
        
        for idx, (chunk_idx, score) in enumerate(similarities[:top_k]):
            chunk_text = chunks[chunk_idx]
            chunk_meta = chunk_metadata[chunk_idx] if chunk_idx < len(chunk_metadata) else {}
            
            context_chunks.append(f"[Source {idx + 1}] {chunk_text}")
            sources.append({
                "page": chunk_meta.get("page", idx + 1),
                "chunk_id": f"chunk_{chunk_idx}",
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
        
        # Stream response
        chat_model = ChatOpenAI(model_name=settings.chat_model)
        async for chunk in chat_model.astream(messages):
            if chunk:
                yield {"type": "content", "content": chunk}

# Create singleton instance
stateless_chat_service = StatelessChatService()