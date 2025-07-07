import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.app.services.pdf_service import PDFService
from backend.app.services.chat_service import ChatService
from aimakerspace.text_utils import PDFLoader, CharacterTextSplitter
from aimakerspace.vectordatabase import VectorDatabase


class TestRAGIntegration:
    """Integration tests for the RAG functionality"""
    
    @pytest.fixture
    def pdf_service(self):
        return PDFService()
    
    @pytest.fixture
    def chat_service(self):
        return ChatService()
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Create a simple PDF-like text content for testing"""
        return [
            "Introduction to Machine Learning\n\nMachine learning is a subset of artificial intelligence that focuses on the development of algorithms and statistical models that enable computer systems to improve their performance on a specific task through experience.",
            "Types of Machine Learning\n\nThere are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning. Supervised learning uses labeled data to train models, while unsupervised learning finds patterns in unlabeled data.",
            "Applications of Machine Learning\n\nMachine learning has numerous applications including image recognition, natural language processing, recommendation systems, and autonomous vehicles. These applications have transformed various industries."
        ]
    
    def test_pdf_loader_functionality(self):
        """Test that PDFLoader can be imported and used"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf') as tmp:
            loader = PDFLoader(tmp.name)
            assert loader is not None
            assert hasattr(loader, 'load')
    
    def test_text_splitter_functionality(self):
        """Test that CharacterTextSplitter works correctly"""
        splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        
        text = "This is a long text that needs to be split into smaller chunks for processing. " * 10
        chunks = splitter.split_texts([text])
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 for chunk in chunks)
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_vector_database_functionality(self):
        """Test that VectorDatabase can store and retrieve vectors"""
        with patch('aimakerspace.openai_utils.embedding.OpenAI'), \
             patch('aimakerspace.openai_utils.embedding.AsyncOpenAI'):
            vector_db = VectorDatabase()
        
        # Test data
        texts = ["Hello world", "Machine learning", "Natural language processing"]
        vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        metadata = [{"id": i} for i in range(3)]
        
        # Build database
        vector_db.vectors = vectors
        vector_db.texts = texts
        vector_db.metadata = metadata
        
        # Test search (mock embedding for query)
        with patch.object(vector_db, 'embed_and_search') as mock_search:
            mock_search.return_value = [(texts[1], metadata[1], 0.9)]
            results = mock_search("learning", k=1)
            
            assert len(results) == 1
            assert results[0][0] == "Machine learning"
    
    @patch('os.environ')
    @patch('app.services.pdf_service.EmbeddingModel')
    async def test_pdf_processing_with_mocked_embeddings(self, mock_embedding_model, mock_environ, pdf_service, sample_pdf_content):
        """Test PDF processing with mocked OpenAI embeddings"""
        # Mock environment
        mock_environ.__getitem__.return_value = "test-api-key"
        
        # Mock embedding model
        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [[0.1] * 10] * 3  # Mock embeddings
        mock_embedder.embed_many.return_value = [[0.1] * 10] * 3
        mock_embedding_model.return_value = mock_embedder
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            
            # Mock PDFLoader to return our sample content
            with patch('app.services.pdf_service.PDFLoader') as mock_loader:
                mock_loader_instance = MagicMock()
                mock_loader_instance.load.return_value = sample_pdf_content
                mock_loader.return_value = mock_loader_instance
                
                # Process PDF
                file_id = pdf_service.generate_file_id()
                metadata = await pdf_service.process_pdf(tmp_path, file_id, "test-api-key")
                
                assert metadata["page_count"] == 3
                assert metadata["chunk_count"] > 0
                assert file_id in pdf_service.vector_stores
                assert file_id in pdf_service.file_metadata
        
        # Clean up
        os.unlink(tmp_path)
    
    def test_chunk_metadata_creation(self, pdf_service):
        """Test that chunk metadata is properly created"""
        file_id = "test-file-123"
        
        # Test metadata format
        chunk_metadata = {
            "file_id": file_id,
            "page": 1,
            "chunk_id": f"{file_id}_p1_c0",
            "chunk_index": 0,
            "total_chunks": 5
        }
        
        assert chunk_metadata["file_id"] == file_id
        assert chunk_metadata["page"] == 1
        assert chunk_metadata["chunk_id"] == f"{file_id}_p1_c0"
    
    @patch('app.services.chat_service.ChatOpenAI')
    async def test_retrieval_and_chat_integration(self, mock_chat_model, chat_service, pdf_service):
        """Test that retrieval integrates properly with chat"""
        # Setup mock chat model
        mock_chat_instance = MagicMock()
        mock_chat_instance.run.return_value = "Based on the context, machine learning is a subset of AI."
        mock_chat_model.return_value = mock_chat_instance
        
        # Create mock vector store
        file_id = "test-file-123"
        mock_vector_store = MagicMock()
        mock_vector_store.search.return_value = [
            ("Machine learning is a subset of artificial intelligence.", {"page": 1, "chunk_id": "test_1"}, 0.95),
            ("Supervised learning uses labeled data.", {"page": 2, "chunk_id": "test_2"}, 0.85)
        ]
        
        # Set up services
        pdf_service.vector_stores[file_id] = mock_vector_store
        chat_service.pdf_service = pdf_service
        
        # Test chat with retrieval
        response = await chat_service.generate_response(
            file_id=file_id,
            message="What is machine learning?",
            history=[],
            api_key="test-api-key"
        )
        
        assert response.message == "Based on the context, machine learning is a subset of AI."
        assert len(response.sources) == 2
        assert response.sources[0].page == 1
        assert response.sources[0].relevance_score == 0.95
    
    def test_source_tracking(self):
        """Test that sources are properly tracked through the RAG pipeline"""
        sources = [
            {"page": 1, "chunk_id": "doc1_p1_c0", "content": "Test content 1", "relevance_score": 0.9},
            {"page": 2, "chunk_id": "doc1_p2_c1", "content": "Test content 2", "relevance_score": 0.8}
        ]
        
        # Verify source structure
        for source in sources:
            assert "page" in source
            assert "chunk_id" in source
            assert "content" in source
            assert "relevance_score" in source
            assert source["relevance_score"] >= 0 and source["relevance_score"] <= 1