"""
PDF Service for Vercel Deployment
Uses Vercel Blob for file storage and KV for metadata/vectors
"""
import os
import uuid
import json
from typing import Dict, Any, List
import logging
from pathlib import Path

from backend.aimakerspace.text_utils import PDFLoader, CharacterTextSplitter
from backend.aimakerspace.openai_utils.embedding import EmbeddingModel
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# For local development without Vercel
try:
    from vercel import blob, kv
    VERCEL_AVAILABLE = True
except ImportError:
    VERCEL_AVAILABLE = False
    logger.warning("Vercel SDK not available, using in-memory storage")

class PDFServiceVercel:
    def __init__(self):
        # For local development fallback
        if not VERCEL_AVAILABLE:
            self.local_vectors = {}
            self.local_metadata = {}
            self.local_chunks = {}
    
    def generate_file_id(self) -> str:
        return str(uuid.uuid4())
    
    async def upload_to_blob(self, file_content: bytes, filename: str) -> str:
        """Upload file to Vercel Blob storage"""
        if VERCEL_AVAILABLE:
            # Upload to Vercel Blob
            result = await blob.put(
                f"pdfs/{filename}",
                file_content,
                {"access": "public"}
            )
            return result.url
        else:
            # Local development: save to uploads directory
            upload_dir = Path(settings.upload_dir)
            upload_dir.mkdir(exist_ok=True)
            file_path = upload_dir / filename
            with open(file_path, 'wb') as f:
                f.write(file_content)
            return str(file_path)
    
    async def process_pdf(self, file_content: bytes, filename: str, file_id: str, api_key: str) -> Dict[str, Any]:
        try:
            # Upload to blob storage
            blob_url = await self.upload_to_blob(file_content, f"{file_id}.pdf")
            
            # For processing, we need a local temp file
            temp_path = f"/tmp/{file_id}.pdf"
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            
            # Load and process PDF
            loader = PDFLoader(temp_path)
            documents = loader.load()
            
            if not documents:
                raise ValueError("No content extracted from PDF")
            
            # Split into chunks
            text_splitter = CharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap
            )
            
            chunks = []
            chunk_metadata = []
            
            for doc_idx, document in enumerate(documents):
                doc_chunks = text_splitter.split(document)
                for chunk_idx, chunk in enumerate(doc_chunks):
                    chunks.append(chunk)
                    chunk_metadata.append({
                        "file_id": file_id,
                        "page": doc_idx + 1,
                        "chunk_id": f"{file_id}_p{doc_idx + 1}_c{chunk_idx}",
                        "chunk_index": chunk_idx,
                        "total_chunks": len(doc_chunks)
                    })
            
            # Create embeddings
            os.environ["OPENAI_API_KEY"] = api_key
            embedding_model = EmbeddingModel(embeddings_model_name=settings.embedding_model)
            embeddings = await embedding_model.async_get_embeddings(chunks)
            
            # Store in KV or local storage
            await self.store_vectors(file_id, chunks, embeddings, chunk_metadata)
            
            # Store metadata
            metadata = {
                "filename": filename,
                "blob_url": blob_url,
                "page_count": len(documents),
                "chunk_count": len(chunks),
                "status": "indexed"
            }
            await self.store_metadata(file_id, metadata)
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return {
                "page_count": len(documents),
                "chunk_count": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Failed to process PDF: {str(e)}")
            raise
    
    async def store_vectors(self, file_id: str, chunks: List[str], embeddings: List[List[float]], metadata: List[Dict]):
        """Store vectors and chunks in KV"""
        if VERCEL_AVAILABLE:
            # Store chunks
            await kv.set(f"chunks:{file_id}", json.dumps(chunks))
            # Store embeddings (as list of lists)
            await kv.set(f"embeddings:{file_id}", json.dumps(embeddings))
            # Store metadata
            await kv.set(f"chunk_metadata:{file_id}", json.dumps(metadata))
        else:
            # Local storage
            self.local_chunks[file_id] = chunks
            self.local_vectors[file_id] = embeddings
            self.local_metadata[f"chunk_metadata:{file_id}"] = metadata
    
    async def store_metadata(self, file_id: str, metadata: Dict[str, Any]):
        """Store file metadata in KV"""
        if VERCEL_AVAILABLE:
            await kv.set(f"file_metadata:{file_id}", json.dumps(metadata))
        else:
            self.local_metadata[f"file_metadata:{file_id}"] = metadata
    
    async def get_file_status(self, file_id: str) -> Dict[str, Any]:
        """Get file status from KV"""
        if VERCEL_AVAILABLE:
            data = await kv.get(f"file_metadata:{file_id}")
            if data:
                metadata = json.loads(data)
                metadata["file_id"] = file_id
                metadata["has_vector_store"] = True
                return metadata
        else:
            metadata = self.local_metadata.get(f"file_metadata:{file_id}")
            if metadata:
                metadata = metadata.copy()
                metadata["file_id"] = file_id
                metadata["has_vector_store"] = True
                return metadata
        return None
    
    async def search_similar_chunks(self, file_id: str, query: str, api_key: str, k: int = 5) -> List[tuple]:
        """Search for similar chunks using embeddings"""
        # Get stored data
        if VERCEL_AVAILABLE:
            chunks_data = await kv.get(f"chunks:{file_id}")
            embeddings_data = await kv.get(f"embeddings:{file_id}")
            
            if not chunks_data or not embeddings_data:
                raise ValueError(f"No indexed document found for file_id: {file_id}")
            
            chunks = json.loads(chunks_data)
            embeddings = json.loads(embeddings_data)
        else:
            chunks = self.local_chunks.get(file_id, [])
            embeddings = self.local_vectors.get(file_id, [])
            
            if not chunks or not embeddings:
                raise ValueError(f"No indexed document found for file_id: {file_id}")
        
        # Get query embedding
        os.environ["OPENAI_API_KEY"] = api_key
        embedding_model = EmbeddingModel(embeddings_model_name=settings.embedding_model)
        query_embedding = await embedding_model.async_get_embedding(query)
        
        # Calculate similarities
        import numpy as np
        similarities = []
        for i, emb in enumerate(embeddings):
            # Cosine similarity
            similarity = np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
            similarities.append((chunks[i], float(similarity)))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]

# Create singleton instance
pdf_service_vercel = PDFServiceVercel()