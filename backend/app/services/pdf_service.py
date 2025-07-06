import os
import uuid
from pathlib import Path
from typing import Dict, Any
import logging

from aimakerspace.text_utils import PDFLoader, CharacterTextSplitter
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel
from app.core.config import settings
from app.core.performance import measure_performance

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        self.vector_stores: Dict[str, VectorDatabase] = {}
        self.file_metadata: Dict[str, Dict[str, Any]] = {}
        
    def generate_file_id(self) -> str:
        return str(uuid.uuid4())
    
    @measure_performance("pdf_processing")
    async def process_pdf(self, file_path: Path, file_id: str, api_key: str) -> Dict[str, Any]:
        try:
            # Load PDF
            logger.info(f"Loading PDF: {file_path}")
            loader = PDFLoader(str(file_path))
            loader.load()
            documents = loader.documents
            
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
            
            logger.info(f"Created {len(chunks)} chunks from PDF")
            
            # Create embeddings
            os.environ["OPENAI_API_KEY"] = api_key
            embedding_model = EmbeddingModel(embeddings_model_name=settings.embedding_model)
            
            # Create vector database with embedding model
            vector_db = VectorDatabase(embedding_model=embedding_model)
            
            # Build the vector database from chunks
            await vector_db.abuild_from_list(chunks)
            
            # Store metadata separately (since VectorDatabase doesn't handle metadata)
            # We'll need to map chunk indices to metadata
            vector_db.metadata = chunk_metadata
            
            # Store in memory
            self.vector_stores[file_id] = vector_db
            self.file_metadata[file_id] = {
                "filename": file_path.name,
                "page_count": len(documents),
                "chunk_count": len(chunks),
                "status": "indexed"
            }
            
            return {
                "page_count": len(documents),
                "chunk_count": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Failed to process PDF: {str(e)}")
            raise
    
    def get_file_status(self, file_id: str) -> Dict[str, Any]:
        if file_id not in self.file_metadata:
            return None
        
        metadata = self.file_metadata[file_id].copy()
        metadata["file_id"] = file_id
        metadata["has_vector_store"] = file_id in self.vector_stores
        
        return metadata
    
    def get_vector_store(self, file_id: str) -> VectorDatabase:
        return self.vector_stores.get(file_id)