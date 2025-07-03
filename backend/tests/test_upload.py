import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import io
import uuid

from app.main import app
from app.models.upload import UploadResponse

client = TestClient(app)

class TestUploadEndpoint:
    
    @pytest.fixture
    def mock_pdf_file(self):
        """Create a mock PDF file for testing"""
        pdf_content = b"%PDF-1.4\n%fake pdf content"
        return io.BytesIO(pdf_content)
    
    @pytest.fixture
    def valid_headers(self):
        """Valid headers with API key"""
        return {"X-API-Key": "sk-test-key-123"}
    
    def test_upload_success(self, mock_pdf_file, valid_headers):
        """Test successful PDF upload"""
        with patch("app.api.endpoints.upload.PDFService") as mock_service:
            # Mock the service response
            mock_instance = mock_service.return_value
            mock_instance.process_pdf = AsyncMock(return_value={
                "file_id": str(uuid.uuid4()),
                "filename": "test.pdf",
                "size": 1024,
                "pages": 5,
                "chunks": 10,
                "processing_time": 1.5
            })
            
            files = {"file": ("test.pdf", mock_pdf_file, "application/pdf")}
            response = client.post("/upload", files=files, headers=valid_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "file_id" in data
            assert data["filename"] == "test.pdf"
            assert data["pages"] == 5
            assert data["chunks"] == 10
    
    def test_upload_missing_api_key(self, mock_pdf_file):
        """Test upload without API key"""
        files = {"file": ("test.pdf", mock_pdf_file, "application/pdf")}
        response = client.post("/upload", files=files)
        
        assert response.status_code == 401
        assert "API key required" in response.json()["detail"]
    
    def test_upload_invalid_api_key(self, mock_pdf_file):
        """Test upload with invalid API key"""
        headers = {"X-API-Key": "invalid-key"}
        files = {"file": ("test.pdf", mock_pdf_file, "application/pdf")}
        response = client.post("/upload", files=files, headers=headers)
        
        assert response.status_code == 401
        assert "Invalid API key format" in response.json()["detail"]
    
    def test_upload_no_file(self, valid_headers):
        """Test upload without file"""
        response = client.post("/upload", headers=valid_headers)
        
        assert response.status_code == 422
        assert "Field required" in str(response.json())
    
    def test_upload_wrong_file_type(self, valid_headers):
        """Test upload with non-PDF file"""
        files = {"file": ("test.txt", io.BytesIO(b"text content"), "text/plain")}
        response = client.post("/upload", files=files, headers=valid_headers)
        
        assert response.status_code == 400
        assert "Only PDF files are allowed" in response.json()["detail"]
    
    def test_upload_empty_file(self, valid_headers):
        """Test upload with empty file"""
        files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
        response = client.post("/upload", files=files, headers=valid_headers)
        
        assert response.status_code == 400
        assert "File is empty" in response.json()["detail"]
    
    def test_upload_large_file(self, valid_headers):
        """Test upload with file exceeding size limit"""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)
        files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
        
        response = client.post("/upload", files=files, headers=valid_headers)
        
        assert response.status_code == 413
        assert "File size exceeds maximum" in response.json()["detail"]
    
    def test_upload_processing_error(self, mock_pdf_file, valid_headers):
        """Test upload when processing fails"""
        with patch("app.api.endpoints.upload.PDFService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.process_pdf = AsyncMock(
                side_effect=Exception("Processing failed")
            )
            
            files = {"file": ("test.pdf", mock_pdf_file, "application/pdf")}
            response = client.post("/upload", files=files, headers=valid_headers)
            
            assert response.status_code == 500
            assert "Failed to process PDF" in response.json()["detail"]
    
    def test_upload_with_special_filename(self, mock_pdf_file, valid_headers):
        """Test upload with special characters in filename"""
        with patch("app.api.endpoints.upload.PDFService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.process_pdf = AsyncMock(return_value={
                "file_id": str(uuid.uuid4()),
                "filename": "test file (2023).pdf",
                "size": 1024,
                "pages": 5,
                "chunks": 10,
                "processing_time": 1.5
            })
            
            files = {"file": ("test file (2023).pdf", mock_pdf_file, "application/pdf")}
            response = client.post("/upload", files=files, headers=valid_headers)
            
            assert response.status_code == 200
            assert response.json()["filename"] == "test file (2023).pdf"
    
    def test_upload_concurrent_requests(self, mock_pdf_file, valid_headers):
        """Test multiple concurrent upload requests"""
        with patch("app.api.endpoints.upload.PDFService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.process_pdf = AsyncMock(return_value={
                "file_id": str(uuid.uuid4()),
                "filename": "test.pdf",
                "size": 1024,
                "pages": 5,
                "chunks": 10,
                "processing_time": 1.5
            })
            
            # Simulate multiple requests
            files = {"file": ("test.pdf", mock_pdf_file, "application/pdf")}
            
            responses = []
            for _ in range(3):
                response = client.post("/upload", files=files, headers=valid_headers)
                responses.append(response)
                # Reset file pointer
                mock_pdf_file.seek(0)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
    
    def test_get_file_status_success(self, valid_headers):
        """Test getting file status"""
        file_id = str(uuid.uuid4())
        
        with patch("app.api.endpoints.upload.PDFService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_file_status = AsyncMock(return_value={
                "file_id": file_id,
                "filename": "test.pdf",
                "status": "processed",
                "uploaded_at": "2024-01-15T10:00:00Z",
                "size": 1024,
                "pages": 5,
                "chunks": 10,
                "vector_count": 10
            })
            
            response = client.get(f"/files/{file_id}", headers=valid_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_id"] == file_id
            assert data["status"] == "processed"
    
    def test_get_file_status_not_found(self, valid_headers):
        """Test getting status for non-existent file"""
        file_id = str(uuid.uuid4())
        
        with patch("app.api.endpoints.upload.PDFService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_file_status = AsyncMock(return_value=None)
            
            response = client.get(f"/files/{file_id}", headers=valid_headers)
            
            assert response.status_code == 404
            assert "File not found" in response.json()["detail"]