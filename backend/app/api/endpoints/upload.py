from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from typing import Dict, Any
import logging
from pathlib import Path

from backend.app.core.config import settings
from backend.app.api.dependencies import get_api_key
from backend.app.services import pdf_service_instance
from backend.app.models.upload import UploadResponse
from backend.app.middleware.rate_limiter import api_key_limiter, RATE_LIMITS
from backend.app.middleware.request_validator import sanitize_filename

logger = logging.getLogger(__name__)
router = APIRouter()

pdf_service = pdf_service_instance

@router.post("/pdf", response_model=UploadResponse)
@api_key_limiter.limit(RATE_LIMITS["upload"])
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key)
) -> UploadResponse:
    # Sanitize filename
    safe_filename = sanitize_filename(file.filename) if file.filename else "unknown.pdf"
    
    # Validate file type
    if not safe_filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Check file size
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    
    if file_size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=413, 
            detail=f"File size exceeds maximum allowed size of {settings.max_upload_size_mb}MB"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(exist_ok=True)
    
    # Save file with unique name
    file_id = pdf_service.generate_file_id()
    file_path = upload_dir / f"{file_id}.pdf"
    
    try:
        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Process and index the PDF
        metadata = await pdf_service.process_pdf(file_path, file_id, api_key)
        
        logger.info(f"Successfully uploaded and processed PDF: {file_id}")
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            size_bytes=len(contents),
            page_count=metadata["page_count"],
            chunk_count=metadata["chunk_count"],
            message="PDF uploaded and indexed successfully"
        )
        
    except Exception as e:
        # Clean up file if processing failed
        if file_path.exists():
            file_path.unlink()
        
        logger.error(f"Failed to process PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process PDF")

@router.get("/pdf/{file_id}/status")
async def get_upload_status(
    file_id: str,
    api_key: str = Depends(get_api_key)
) -> Dict[str, Any]:
    status = pdf_service.get_file_status(file_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="File not found")
    
    return status