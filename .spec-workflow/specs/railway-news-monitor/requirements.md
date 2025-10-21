# Requirements Document

## Introduction

The Railway News Monitor system is an automated web scraping and monitoring tool designed to track and analyze Taiwan Railway Administration (TRA) public announcements. This system serves academic research by capturing the complete lifecycle of service disruption announcements (caused by typhoons, earthquakes, heavy rain, etc.), tracking their publication patterns, update frequencies, and content evolution over time.

The system addresses critical research needs by:
- Automatically detecting and tagging announcements related to train service interruptions
- Tracking both new announcements (Report #1, #2, #3...) and in-place content modifications
- Recording precise timestamps for temporal analysis of response patterns
- **Parsing announcement content to extract structured data** (e.g., predicted resumption times, affected lines, report versions) for programmatic analysis of how crisis information evolves

## Alignment with Product Vision

This system enables Professor Lin's research on crisis communication patterns by providing comprehensive, timestamped data on how TRA communicates service disruptions to the public. The automated monitoring eliminates manual tracking efforts and ensures complete data capture during critical events.

## Requirements

### Requirement 1: Historical Data Collection

**User Story:** As a researcher, I want to collect all existing TRA announcements from the archive, so that I can establish a baseline dataset for historical analysis.

#### Acceptance Criteria

1. WHEN the initial scrape is triggered THEN the system SHALL iterate through all list pages starting from page=0 until no data is returned
2. WHEN processing each list page THEN the system SHALL extract title, publish_date, detail_url, and newsNo for each announcement
3. WHEN visiting each detail page THEN the system SHALL compute a content hash (MD5 or SHA256) of the HTML content and execute the structured data extraction process (Requirement 7)
4. WHEN storing initial data THEN the system SHALL record scraped_at timestamp in ISO 8601 format and include the extracted_data object in version_history
5. WHEN completing historical scrape THEN the system SHALL save all data to master.json in the specified structure (Requirement 6)

### Requirement 2: Incremental Monitoring

**User Story:** As a researcher, I want the system to continuously monitor new announcements, so that I can capture real-time updates during service disruption events.

#### Acceptance Criteria

1. WHEN the monitoring job executes THEN the system SHALL fetch only the first 1-2 list pages to optimize performance
2. WHEN encountering a newsNo not in the database THEN the system SHALL classify it as a new announcement and perform full data extraction (including classification and structured data extraction per Requirement 7)
3. WHEN encountering an existing newsNo THEN the system SHALL re-fetch the detail page and compute a new content hash
4. IF the new hash differs from the latest version_history hash THEN the system SHALL run the full extraction process (Requirement 7) and append a new version record (Requirement 6) with all data including extracted_data
5. IF the new hash matches the existing hash THEN the system SHALL skip processing and continue to the next announcement
6. WHEN the monitoring job is configured THEN the system SHALL execute at intervals of 5 minutes (configurable)

### Requirement 3: Content Change Detection

**User Story:** As a researcher, I want to detect when TRA modifies existing announcements, so that I can analyze how crisis communications evolve over time.

#### Acceptance Criteria

1. WHEN computing content hash THEN the system SHALL use MD5 or SHA256 algorithm on the detail page HTML content
2. WHEN a content change is detected THEN the system SHALL preserve all previous versions in the version_history array
3. WHEN appending a new version THEN the system SHALL include scraped_at, content_html, content_hash, and the newly generated extracted_data object
4. WHEN comparing hashes THEN the system SHALL use the most recent version_history entry as the reference
5. IF the title is modified THEN the system SHALL optionally update the top-level title field

### Requirement 4: Announcement Classification

**User Story:** As a researcher, I want announcements automatically tagged by category, so that I can filter for service-disruption-related events without manual review.

#### Acceptance Criteria

1. WHEN processing any announcement THEN the system SHALL scan both title and content_html for classification keywords
2. WHEN keywords match disruption patterns ['停駛', '暫停營運', '中斷', '落石', '出軌'] THEN the system SHALL set category to "Disruption_Suspension"
3. WHEN keywords match update patterns ['第2報', '第3報', '第N報'] THEN the system SHALL set category to "Disruption_Update"
4. WHEN keywords match resumption patterns ['恢復行駛', '恢復通車', '已排除'] THEN the system SHALL set category to "Disruption_Resumption"
5. WHEN keywords match weather patterns ['颱風', '豪雨', '地震'] THEN the system SHALL add weather-related tags
6. WHEN classification is complete THEN the system SHALL store category and matched keywords in the classification object

### Requirement 5: Event Grouping

**User Story:** As a researcher, I want related announcements (Report #1, #2, #3...) grouped under a single event ID, so that I can reconstruct the complete timeline of a service disruption.

#### Acceptance Criteria

1. WHEN processing a classified announcement THEN the system SHALL attempt to extract event name from the title (e.g., "平溪線豪雨", "樺加沙颱風")
2. WHEN an event name is identified THEN the system SHALL combine it with publish_date to generate event_group_id (format: "YYYYMMDD_EventName")
3. WHEN storing the announcement THEN the system SHALL include event_group_id in the classification object
4. IF multiple announcements share the same event_group_id THEN researchers SHALL be able to filter and analyze them as a cohesive event sequence

### Requirement 6: Data Persistence

**User Story:** As a researcher, I want all announcement data stored in a structured JSON format, so that I can perform programmatic analysis and export.

#### Acceptance Criteria

1. WHEN storing data THEN the system SHALL use a JSON file named master.json
2. WHEN structuring each announcement THEN the system SHALL include fields: id, title, publish_date, detail_url, classification, and version_history
3. WHEN storing version_history THEN each entry SHALL include scraped_at, content_html, content_hash, and extracted_data (as defined in Requirement 8)
4. WHEN updating existing announcements THEN the system SHALL append to version_history without overwriting previous versions
5. WHEN writing to JSON THEN the system SHALL maintain valid JSON structure and UTF-8 encoding

#### Version History Structure

Each entry in the `version_history` array SHALL follow this structure:

```json
{
  "scraped_at": "2025-08-12T20:40:00Z",
  "content_html": "<div>...內文...8月13日12時前...</div>",
  "content_hash": "md5:a1b2c3d4...",
  "extracted_data": {
    "report_version": "2",
    "event_type": "Typhoon",
    "status": "Partial_Suspension",
    "affected_lines": ["西部幹線", "東部幹線"],
    "affected_stations": [],
    "predicted_resumption_time": "2025-08-13T12:00:00Z",
    "actual_resumption_time": null
  }
}
```

### Requirement 7: Structured Data Extraction

**User Story:** As a researcher, I want the system to parse the announcement content and extract key structured data points (like resumption times, affected stations, and report versions), so that I can programmatically analyze the evolution of an event without reading the raw HTML.

#### Acceptance Criteria

1. WHEN processing any new version in version_history THEN the system SHALL execute a "Content Parsing" function on the content_html
2. WHEN parsing content THEN the system SHALL use a library of Regular Expressions (RegEx) and keywords to find and extract key data
3. WHEN extracting data THEN the system SHALL attempt to populate the following fields:
   - **report_version**: Report number (e.g., "1", "2", "第3發")
   - **event_type**: Event category (e.g., "Typhoon", "Heavy_Rain", "Equipment_Failure", "Earthquake")
   - **status**: Current operational status (e.g., "Suspended", "Partial_Operation", "Resumed_Single_Track", "Resumed_Normal")
   - **affected_lines**: List of affected railway lines (e.g., ["西部幹線", "東部幹線", "南迴線"])
   - **affected_stations**: List of affected stations (e.g., ["二水", "林內"])
   - **predicted_resumption_time**: Estimated resumption time (e.g., "2025-07-27T19:00:00Z") - **KEY DATA POINT**
   - **actual_resumption_time**: Actual resumption time (e.g., "2025-07-08T17:28:00Z")
4. IF parsing fails to find a value for a field THEN the field SHALL be populated with null
5. IF the parsing logic fails entirely THEN the extracted_data object SHALL be null and the error SHALL be logged

#### Research Priority

The **predicted_resumption_time** field is the primary research target. The system must track how this value evolves across:
- Sequential reports (Report #1 → Report #2 → Report #3...)
- In-place modifications (same announcement, updated content)

This enables analysis of how TRA's time estimates change during crisis events (e.g., "19:00 通車" → "20:00 通車").

### Requirement 8: Error Handling and Resilience

**User Story:** As a system operator, I want the scraper to handle network errors gracefully, so that temporary failures don't corrupt the dataset.

#### Acceptance Criteria

1. WHEN a network request fails THEN the system SHALL retry up to 3 times with exponential backoff
2. IF all retries fail THEN the system SHALL log the error and continue processing other announcements
3. WHEN encountering malformed HTML THEN the system SHALL log the error and skip that specific announcement
4. WHEN JSON write operations fail THEN the system SHALL preserve the previous valid state
5. WHEN the monitoring job encounters errors THEN it SHALL continue on the next scheduled execution

## Non-Functional Requirements

### Code Architecture and Modularity
- **Single Responsibility Principle**: Separate modules for scraping, classification, hashing, content parsing, and storage
- **Modular Design**: Extractor (list/detail page parsing), Classifier (keyword matching), Content Parser (structured data extraction), Storage Manager (JSON operations)
- **Dependency Management**: Minimize coupling between scraping logic, parsing logic, and storage format
- **Clear Interfaces**: Define contracts between scraper, classifier, content parser, and storage components

### Performance
- Historical scrape SHALL complete within reasonable time (estimated 5-10 minutes for 500 pages)
- Monitoring cycle SHALL complete within 1-2 minutes to maintain 5-minute intervals
- Hash computation SHALL use optimized algorithms (MD5 preferred for speed)
- JSON file operations SHALL use incremental writes to avoid loading entire file into memory

### Security
- The system SHALL respect robots.txt directives
- Request rate SHALL be limited to avoid overwhelming TRA servers (recommended: 1 request per second)
- User-Agent header SHALL identify the scraper appropriately

### Reliability
- The system SHALL maintain data integrity during crashes (atomic JSON writes)
- The system SHALL support resumption of historical scrape if interrupted
- Monitoring jobs SHALL be idempotent (re-running produces same results)

### Usability
- Configuration SHALL be externalized (scrape intervals, page limits, keyword lists)
- Logs SHALL provide clear visibility into scraping progress and errors
- Output JSON SHALL be human-readable (formatted with indentation)
