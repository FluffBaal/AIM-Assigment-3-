import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
import uuid
from typing import List, AsyncGenerator

from app.main import app
from app.models.chat import ChatMessage, ChatSource

client = TestClient(app)

class TestChatEndpoint:
    
    @pytest.fixture
    def valid_headers(self):
        """Valid headers with API key"""
        return {"X-API-Key": "sk-test-key-123"}
    
    @pytest.fixture
    def chat_request(self):
        """Sample chat request"""
        return {
            "file_id": str(uuid.uuid4()),
            "message": "What is this document about?",
            "history": []
        }
    
    def test_chat_success_non_streaming(self, valid_headers, chat_request):
        """Test successful non-streaming chat"""
        with patch("app.api.endpoints.chat.ChatService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.chat = AsyncMock(return_value={
                "response": "This document is about testing.",
                "sources": [
                    {
                        "page": 1,
                        "text": "Testing is important...",
                        "relevance_score": 0.9
                    }
                ]
            })
            
            response = client.post("/chat", json=chat_request, headers=valid_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "sources" in data
            assert len(data["sources"]) == 1
            assert data["sources"][0]["page"] == 1
    
    def test_chat_success_streaming(self, valid_headers, chat_request):
        """Test successful streaming chat"""
        async def mock_stream():
            yield {"type": "content", "content": "This is "}
            yield {"type": "content", "content": "a test."}
            yield {"type": "sources", "sources": [{"page": 1, "text": "Test", "relevance_score": 0.8}]}
            yield {"type": "done"}
        
        with patch("app.api.endpoints.chat.ChatService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.stream_chat = mock_stream
            
            headers = {**valid_headers, "Accept": "text/event-stream"}
            response = client.post("/chat", json=chat_request, headers=headers)
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            # Parse SSE response
            events = response.text.strip().split("\n\n")
            assert len(events) > 0
            
            # Check first event
            first_event_lines = events[0].split("\n")
            assert first_event_lines[0] == "event: content"
            assert first_event_lines[1].startswith("data: ")
    
    def test_chat_missing_api_key(self, chat_request):
        """Test chat without API key"""
        response = client.post("/chat", json=chat_request)
        
        assert response.status_code == 401
        assert "API key required" in response.json()["detail"]
    
    def test_chat_invalid_file_id(self, valid_headers):
        """Test chat with invalid file ID format"""
        request = {
            "file_id": "invalid-id",
            "message": "Test",
            "history": []
        }
        
        response = client.post("/chat", json=request, headers=valid_headers)
        
        assert response.status_code == 422
    
    def test_chat_empty_message(self, valid_headers):
        """Test chat with empty message"""
        request = {
            "file_id": str(uuid.uuid4()),
            "message": "",
            "history": []
        }
        
        response = client.post("/chat", json=request, headers=valid_headers)
        
        assert response.status_code == 422
        assert "at least 1 character" in str(response.json())
    
    def test_chat_with_history(self, valid_headers):
        """Test chat with conversation history"""
        request = {
            "file_id": str(uuid.uuid4()),
            "message": "Follow up question",
            "history": [
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": "First answer"}
            ]
        }
        
        with patch("app.api.endpoints.chat.ChatService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.chat = AsyncMock(return_value={
                "response": "Follow up answer",
                "sources": []
            })
            
            response = client.post("/chat", json=request, headers=valid_headers)
            
            assert response.status_code == 200
            # Verify history was passed to service
            mock_instance.chat.assert_called_once()
            call_args = mock_instance.chat.call_args[1]
            assert len(call_args["history"]) == 2
    
    def test_chat_file_not_found(self, valid_headers, chat_request):
        """Test chat with non-existent file"""
        with patch("app.api.endpoints.chat.ChatService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.chat = AsyncMock(
                side_effect=ValueError("File not found")
            )
            
            response = client.post("/chat", json=chat_request, headers=valid_headers)
            
            assert response.status_code == 404
            assert "File not found" in response.json()["detail"]
    
    def test_chat_processing_error(self, valid_headers, chat_request):
        """Test chat when processing fails"""
        with patch("app.api.endpoints.chat.ChatService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.chat = AsyncMock(
                side_effect=Exception("Internal error")
            )
            
            response = client.post("/chat", json=chat_request, headers=valid_headers)
            
            assert response.status_code == 500
            assert "Chat processing failed" in response.json()["detail"]
    
    def test_chat_long_message(self, valid_headers):
        """Test chat with very long message"""
        request = {
            "file_id": str(uuid.uuid4()),
            "message": "x" * 1000,  # 1000 character message
            "history": []
        }
        
        with patch("app.api.endpoints.chat.ChatService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.chat = AsyncMock(return_value={
                "response": "Response to long message",
                "sources": []
            })
            
            response = client.post("/chat", json=request, headers=valid_headers)
            
            assert response.status_code == 200
    
    def test_chat_invalid_history_format(self, valid_headers):
        """Test chat with invalid history format"""
        request = {
            "file_id": str(uuid.uuid4()),
            "message": "Test",
            "history": [
                {"role": "invalid", "content": "Test"}  # Invalid role
            ]
        }
        
        response = client.post("/chat", json=request, headers=valid_headers)
        
        assert response.status_code == 422
    
    def test_chat_streaming_error(self, valid_headers, chat_request):
        """Test streaming chat with error during stream"""
        async def mock_stream_with_error():
            yield {"type": "content", "content": "Starting..."}
            raise Exception("Stream error")
        
        with patch("app.api.endpoints.chat.ChatService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.stream_chat = mock_stream_with_error
            
            headers = {**valid_headers, "Accept": "text/event-stream"}
            response = client.post("/chat", json=chat_request, headers=headers)
            
            # Should still return 200 but with error in stream
            assert response.status_code == 200
            
            # Check that error event is in response
            assert "event: error" in response.text
    
    def test_chat_with_multiple_sources(self, valid_headers, chat_request):
        """Test chat response with multiple sources"""
        with patch("app.api.endpoints.chat.ChatService") as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.chat = AsyncMock(return_value={
                "response": "Based on multiple sources...",
                "sources": [
                    {
                        "page": 1,
                        "text": "First source",
                        "relevance_score": 0.95,
                        "chunk_id": "chunk-1"
                    },
                    {
                        "page": 3,
                        "text": "Second source",
                        "relevance_score": 0.87,
                        "chunk_id": "chunk-2"
                    },
                    {
                        "page": 5,
                        "text": "Third source",
                        "relevance_score": 0.82,
                        "chunk_id": "chunk-3"
                    }
                ]
            })
            
            response = client.post("/chat", json=chat_request, headers=valid_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["sources"]) == 3
            
            # Verify sources are sorted by relevance
            scores = [s["relevance_score"] for s in data["sources"]]
            assert scores == sorted(scores, reverse=True)
    
    def test_chat_rate_limiting(self, valid_headers, chat_request):
        """Test rate limiting on chat endpoint"""
        # This would require implementing rate limiting in the app
        # For now, just test that multiple requests work
        responses = []
        for _ in range(5):
            with patch("app.api.endpoints.chat.ChatService") as mock_service:
                mock_instance = mock_service.return_value
                mock_instance.chat = AsyncMock(return_value={
                    "response": "Test response",
                    "sources": []
                })
                
                response = client.post("/chat", json=chat_request, headers=valid_headers)
                responses.append(response)
        
        # All should succeed without rate limiting
        for response in responses:
            assert response.status_code == 200