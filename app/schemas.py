import re
from typing import List, Literal, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator

# Regex matching standard web URLs (http, https, or www)
URL_REGEX = re.compile(
    r'(?:https?://|www\.)[a-zA-Z0-9_\-]+(?:\.[a-zA-Z0-9_\-]+)*(?:\.[a-zA-Z]{2,}|:\d+)(?:/[^\s<>"]*)?',
    re.IGNORECASE
)

# Hostname validation regex
HOSTNAME_REGEX = re.compile(
    r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$|^localhost$'
)


def extract_and_validate_urls(text: str) -> str:
    """
    Extracts URLs from text, asserts exactly one URL exists,
    and validates its structure and hostname.
    """
    matches = URL_REGEX.findall(text)
    
    if len(matches) == 0:
        raise ValueError("Message must contain exactly one Call-To-Action (CTA) link, but none was found.")
    
    if len(matches) > 1:
        raise ValueError(
            f"Message must contain exactly one Call-To-Action (CTA) link, but {len(matches)} were found: {', '.join(matches)}"
        )
    
    raw_url = matches[0]
    
    # Normalize url if entered as www.
    target_url = raw_url if raw_url.lower().startswith(('http://', 'https://')) else f"https://{raw_url}"
    
    parsed = urlparse(target_url)
    if not parsed.scheme or parsed.scheme.lower() not in ('http', 'https'):
        raise ValueError(f"Invalid URL scheme '{parsed.scheme}'. Only 'http' and 'https' are supported.")
    
    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"Invalid URL '{raw_url}': missing valid domain/host.")
    
    # Strip port if present for hostname check
    if not HOSTNAME_REGEX.match(hostname):
        raise ValueError(f"Invalid domain/host '{hostname}' in URL '{raw_url}'.")
    
    return target_url


class PostingRequest(BaseModel):
    message: str = Field(
        ...,
        description="The content to publish. Must contain exactly one CTA link and be <= 200 characters.",
        json_schema_extra={
            "example": "Check out our latest business platform and grow your online visibility. https://example.com"
        }
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or contain only whitespace.")
        
        cleaned = v.strip()
        
        if len(cleaned) > 200:
            raise ValueError(
                f"Message length is {len(cleaned)} characters, which exceeds the maximum limit of 200 characters."
            )
        
        # Validates CTA count == 1 and URL syntax
        extract_and_validate_urls(cleaned)
        
        return cleaned


class PlatformResult(BaseModel):
    platform: str = Field(..., description="Platform name")
    status: Literal["success", "failed"] = Field(..., description="Success or Failed")
    posted_url: Optional[str] = Field(None, description="Published content URL")
    public_access: bool = Field(False, description="Whether content is publicly accessible")
    date: Optional[str] = Field(None, description="Posting date (YYYY-MM-DD)")
    time: Optional[str] = Field(None, description="Posting time (HH:MM:SS)")
    error: Optional[str] = Field(None, description="Error details, if applicable")


class PostingResponse(BaseModel):
    success: bool = Field(..., description="True if posting workflow completed and at least one platform succeeded")
    results: List[PlatformResult] = Field(..., description="Posting results for all integrated platforms")
