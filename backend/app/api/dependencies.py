from fastapi import Header, HTTPException
from typing import Optional

async def get_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is required. Please provide your OpenAI API key in the X-API-Key header."
        )
    
    # Validate that the API key looks like an OpenAI key
    if not x_api_key.startswith("sk-"):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key format. Please provide a valid OpenAI API key."
        )
    
    return x_api_key