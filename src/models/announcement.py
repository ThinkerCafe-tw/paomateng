"""
Pydantic models for TRA announcement data structures
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class AnnouncementListItem(BaseModel):
    """
    Represents an announcement item from the TRA list page
    """
    news_no: str = Field(..., description="Unique ID from URL newsNo parameter")
    title: str = Field(..., description="Announcement title")
    publish_date: str = Field(..., description="Publication date in YYYY/MM/DD format")
    detail_url: str = Field(..., description="Full URL to detail page")


class ExtractedData(BaseModel):
    """
    Structured data extracted from announcement HTML content
    """
    report_version: Optional[str] = Field(None, description="Report number (e.g., '1', '2', '第3發')")
    event_type: Optional[str] = Field(None, description="Event category (e.g., 'Typhoon', 'Heavy_Rain', 'Equipment_Failure', 'Earthquake')")
    status: Optional[str] = Field(None, description="Current operational status (e.g., 'Suspended', 'Partial_Operation', 'Resumed_Single_Track', 'Resumed_Normal')")
    affected_lines: List[str] = Field(default_factory=list, description="List of affected railway lines")
    affected_stations: List[str] = Field(default_factory=list, description="List of affected stations")
    predicted_resumption_time: Optional[datetime] = Field(None, description="Estimated resumption time (ISO 8601, timezone-aware)")
    actual_resumption_time: Optional[datetime] = Field(None, description="Actual resumption time (ISO 8601, timezone-aware)")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Classification(BaseModel):
    """
    Classification metadata for announcements
    """
    category: str = Field(..., description="Announcement category (e.g., 'Disruption_Suspension', 'Disruption_Update', 'Disruption_Resumption', 'General_Operation')")
    keywords: List[str] = Field(default_factory=list, description="Matched keywords from classification")
    event_group_id: str = Field(..., description="Event group identifier (format: YYYYMMDD_EventName)")


class VersionEntry(BaseModel):
    """
    Represents a single version/snapshot of an announcement
    """
    scraped_at: datetime = Field(..., description="Timestamp when this version was scraped (ISO 8601, timezone-aware)")
    content_html: str = Field(..., description="Raw HTML content of the announcement")
    content_text: Optional[str] = Field(default=None, description="Plain text content with preserved formatting (paragraphs and line breaks)")
    content_hash: str = Field(..., description="MD5 hash of content_html (format: 'md5:<hexdigest>')")
    extracted_data: Optional[ExtractedData] = Field(default=None, description="Structured data extracted from content_html")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Announcement(BaseModel):
    """
    Complete announcement record with version history
    """
    id: str = Field(..., description="Unique identifier (same as news_no)")
    title: str = Field(..., description="Announcement title")
    publish_date: str = Field(..., description="Publication date in YYYY/MM/DD format")
    detail_url: str = Field(..., description="Full URL to detail page")
    classification: Classification = Field(..., description="Classification metadata")
    version_history: List[VersionEntry] = Field(default_factory=list, description="Version history with all snapshots")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
