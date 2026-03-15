from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PlatformEnum(str, Enum):
    """
    Platforms Included
    """
    AMAZON = "amazon"
    FLIPKART = "flipkart"

class ScrapperRequest(BaseModel):
    """
    Scrapper Request Model
    """
    # ... denotes field required
    platform: List[PlatformEnum] = Field(default=PlatformEnum.AMAZON, description="E-commerce platform to scrape from")
    product_name: str = Field(..., description="Name of the product to be scraped", min_length=2, max_length=100),
    category: Optional[str] = Field(None, description="Category of the product"),
    deep_details: bool = Field(True, description="Flag to include deep details in the scraping process"),
    max_products: int = Field(80, description="Maximum number of products to scrape", ge=1, le=500),
    include_reviews: bool = Field(False, description="Flag to include reviews in the scraping process")
    auto_generate_insights: bool = Field(False, description="Flag to automatically generate insights after scraping completes")

class ScrapperResponse(BaseModel):
    """
    Scrapper Response Model
    """
    status: str 
    message: str
    search_id: str
    data_path: Optional[str] = None # Path to the stored data file

class ScrapperStatus(BaseModel):
    """
    Scrapper Status Model
    """
    search_id: str
    user_id: str
    platform: List[PlatformEnum]
    product_name: str
    status: str
    deep_details: int
    include_reviews: int
    max_products: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    progress: float = Field(0.0, description="Progress percentage of the scraping task"),
    output_file_name: Optional[str] = None # Name of the output file where data is stored
    total_products_scraped: Optional[int] = Field(0, description="Total number of products scraped")
    insight_generated: bool = Field(False, description="Whether insights have been generated")
    data_quality_passed: bool = Field(True, description="Whether data quality checks passed")

class ScrappedData(BaseModel):
    """
    Scrapped Data Model
    """
    search_id: str
    product_name: str
    user_id: str
    deep_details: int
    include_reviews: int
    platform: List[PlatformEnum]
    output_file_name: str
    status: str
    completed_at: Optional[datetime] = None
    total_products_scraped: Optional[int] = Field(0, description="Total number of products scraped")
    insight_generated: bool = Field(False, description="Whether insights have been generated")
    data_quality_passed: bool = Field(True, description="Whether data quality checks passed")

class SearchStatistics(BaseModel):
    """
    Search Statistics Model - Aggregated statistics for user searches
    """
    total: int = Field(description="Total number of searches")
    completed: int = Field(description="Number of completed searches")
    in_progress: int = Field(description="Number of in-progress or pending searches")
    failed: int = Field(description="Number of failed searches")

