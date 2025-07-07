"""
Stateless PDF Service for Vercel Deployment
Returns all data to client, no server-side storage needed
"""
import os
import uuid
from typing import Dict, Any
import logging

from aimakerspace.text_utils import PDFLoader, CharacterTextSplitter
from aimakerspace.openai_utils.embedding import EmbeddingModel
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class StatelessPDFService:
    """
    Processes PDFs and returns all data to the client.
    No server-side storage required.
    """
    
    def generate_file_id(self) -> str:
        return str(uuid.uuid4())
    
    async def process_pdf_and_return_data(self, file_content: bytes, filename: str, api_key: str) -> Dict[str, Any]:
        """
        Process PDF and return all data needed for chat.
        Client will store this data.
        """
        try:
            file_id = self.generate_file_id()
            
            # Save to /tmp for processing (Vercel allows this)
            temp_path = f"/tmp/{file_id}.pdf"
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            
            # Load and process PDF
            logger.info(f"Loading PDF: {temp_path}")
            loader = PDFLoader(temp_path)
            documents = loader.load()
            
            if not documents:
                raise ValueError("No content extracted from PDF")
            
            logger.info(f"Loaded {len(documents)} pages from PDF")
            
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
                        "page": doc_idx + 1,
                        "chunk_index": chunk_idx,
                        "total_chunks": len(doc_chunks)
                    })
            
            logger.info(f"Created {len(chunks)} chunks from PDF")
            
            # Create embeddings
            os.environ["OPENAI_API_KEY"] = api_key
            embedding_model = EmbeddingModel(embeddings_model_name=settings.embedding_model)
            embeddings = await embedding_model.async_get_embeddings(chunks)
            
            logger.info(f"Generated embeddings for {len(chunks)} chunks")
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            # Return all data to client
            return {
                "file_id": file_id,
                "filename": filename,
                "page_count": len(documents),
                "chunk_count": len(chunks),
                "chunks": chunks,
                "embeddings": embeddings,  # List of lists (vectors)
                "chunk_metadata": chunk_metadata,
                "message": "PDF processed successfully. Data returned for client-side storage."
            }
            
        except Exception as e:
            logger.error(f"Failed to process PDF: {str(e)}")
            # Clean up temp file on error
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            raise

# Create singleton instance
stateless_pdf_service = StatelessPDFService()