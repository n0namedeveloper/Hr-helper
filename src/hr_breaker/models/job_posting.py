from pydantic import BaseModel, Field


class JobPosting(BaseModel):
    """Structured job posting data."""

    title: str = Field(default="", description="Job title")
    company: str = Field(default="", description="Company name")
    requirements: list[str] = Field(default_factory=list, description="Requirements")
    keywords: list[str] = Field(default_factory=list, description="Keywords")
    description: str = Field(default="", description="Job description")
    raw_text: str = Field(default="", description="Raw job posting text")
    
    model_config = {
        "extra": "ignore",  # Ignore extra fields from LLM
    }
