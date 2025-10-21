"""
Monitoring orchestrator for incremental updates
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from src.utils.http_client import HTTPClient
from src.utils.text_utils import html_to_text
from src.scrapers.list_scraper import ListScraper
from src.scrapers.detail_scraper import DetailScraper
from src.parsers.content_parser import ContentParser
from src.classifiers.announcement_classifier import AnnouncementClassifier
from src.storage.json_storage import JSONStorage
from src.models.announcement import Announcement, VersionEntry


def run_monitoring_cycle(config: dict) -> None:
    """
    Run single monitoring cycle to detect new/updated announcements

    Args:
        config: Configuration dictionary from settings.yaml
    """
    logger.info("Running monitoring cycle...")

    # Initialize components
    http_client = HTTPClient(
        user_agent=config["scraper"]["user_agent"],
        timeout=config["scraper"]["request_timeout"],
        retry_attempts=config["scraper"]["retry_attempts"],
        rate_limit_delay=config["scraper"]["rate_limit_delay"],
    )

    list_scraper = ListScraper(http_client, config["scraper"]["base_url"])
    detail_scraper = DetailScraper(http_client)
    content_parser = ContentParser()
    classifier = AnnouncementClassifier()
    storage = JSONStorage(
        output_file=config["storage"]["output_file"],
        backup_dir=config["storage"]["backup_dir"],
        pretty_print=config["storage"]["pretty_print"],
    )

    try:
        # Step 1: Scrape first few pages only
        max_pages = config["monitoring"]["max_pages_to_check"]
        logger.info(f"Checking first {max_pages} page(s) for updates...")

        all_items = []
        for page_num in range(max_pages):
            items = list_scraper.scrape_page(page_num)
            if not items:
                break
            all_items.extend(items)

        logger.info(f"Found {len(all_items)} announcements to check")

        # Step 2: Load existing data once (performance optimization)
        existing_announcements = storage.load()
        existing_by_id = {ann.id: ann for ann in existing_announcements}
        logger.debug(f"Loaded {len(existing_by_id)} existing announcements into memory")

        # Step 3: Check each announcement
        new_count = 0
        updated_count = 0

        for item in all_items:
            try:
                # Check if announcement exists
                existing = existing_by_id.get(item.news_no)

                if existing is None:
                    # Case A: New announcement
                    logger.info(f"NEW announcement detected: {item.news_no} - {item.title}")

                    # Scrape detail page
                    detail_result = detail_scraper.scrape_detail(item.detail_url)
                    if not detail_result:
                        logger.warning(f"Failed to scrape detail for {item.news_no}, skipping")
                        continue

                    content_html, content_hash = detail_result

                    # Parse and classify
                    extracted_data = content_parser.parse(content_html)
                    classification = classifier.classify(item.title, content_html)
                    classification.event_group_id = classifier.extract_event_group_id(
                        item.title, item.publish_date
                    )

                    # Create new announcement
                    version_entry = VersionEntry(
                        scraped_at=datetime.now(ZoneInfo("Asia/Taipei")),
                        content_html=content_html,
                        content_text=html_to_text(content_html),
                        content_hash=content_hash,
                        extracted_data=extracted_data,
                    )

                    announcement = Announcement(
                        id=item.news_no,
                        title=item.title,
                        publish_date=item.publish_date,
                        detail_url=item.detail_url,
                        classification=classification,
                        version_history=[version_entry],
                    )

                    storage.add_announcement(announcement)
                    new_count += 1

                else:
                    # Case B: Existing announcement - check for changes
                    detail_result = detail_scraper.scrape_detail(item.detail_url)
                    if not detail_result:
                        continue

                    content_html, new_hash = detail_result

                    # Get latest hash from version history
                    latest_hash = existing.version_history[-1].content_hash

                    if new_hash != latest_hash:
                        # Content changed!
                        logger.info(f"CHANGE detected: {item.news_no} - {item.title}")
                        logger.debug(f"Old hash: {latest_hash}, New hash: {new_hash}")

                        # Parse new content
                        extracted_data = content_parser.parse(content_html)

                        # Create new version entry
                        new_version = VersionEntry(
                            scraped_at=datetime.now(ZoneInfo("Asia/Taipei")),
                            content_html=content_html,
                            content_text=html_to_text(content_html),
                            content_hash=new_hash,
                            extracted_data=extracted_data,
                        )

                        # Append to version history
                        storage.append_version(item.news_no, new_version)
                        updated_count += 1

            except Exception as e:
                logger.error(f"Error processing {item.news_no}: {e}")
                continue

        logger.info(f"Monitoring cycle complete: {new_count} new, {updated_count} updated")

    except Exception as e:
        logger.error(f"Monitoring cycle failed: {e}")
    finally:
        http_client.close()


def start_monitoring(config: dict) -> None:
    """
    Start background monitoring with scheduler

    Args:
        config: Configuration dictionary from settings.yaml
    """
    interval_minutes = config["monitoring"]["interval_minutes"]

    logger.info("=" * 80)
    logger.info("Starting Monitoring Mode")
    logger.info(f"Interval: Every {interval_minutes} minutes")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)

    # Create scheduler
    scheduler = BackgroundScheduler()

    # Schedule monitoring job
    scheduler.add_job(
        run_monitoring_cycle,
        "interval",
        minutes=interval_minutes,
        args=[config],
        id="monitoring_job",
    )

    # Run first cycle immediately
    run_monitoring_cycle(config)

    # Start scheduler
    scheduler.start()

    try:
        # Keep main thread alive
        import time
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping monitoring...")
        scheduler.shutdown()
        logger.info("Monitoring stopped")
