"""
HTTP client with retry logic and rate limiting for web scraping
"""

import time
from typing import Optional
import requests
from loguru import logger


class HTTPClient:
    """
    HTTP client with retry logic, rate limiting, and error handling
    """

    def __init__(
        self,
        user_agent: str,
        timeout: int = 30,
        retry_attempts: int = 3,
        rate_limit_delay: float = 1.0,
    ):
        """
        Initialize HTTP client

        Args:
            user_agent: User-Agent string for requests
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts on failure
            rate_limit_delay: Delay between requests in seconds
        """
        self.user_agent = user_agent
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time: Optional[float] = None

        # Create session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def _apply_rate_limit(self) -> None:
        """
        Apply rate limiting between requests
        """
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - elapsed
                time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get(self, url: str) -> Optional[requests.Response]:
        """
        Perform GET request with retry logic

        Args:
            url: URL to fetch

        Returns:
            Response object if successful, None if all retries fail
        """
        for attempt in range(1, self.retry_attempts + 1):
            try:
                self._apply_rate_limit()

                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                logger.debug(f"Successfully fetched {url}")
                return response

            except requests.exceptions.Timeout:
                logger.warning(
                    f"Timeout on attempt {attempt}/{self.retry_attempts} for {url}"
                )
                if attempt < self.retry_attempts:
                    backoff_time = 2 ** (attempt - 1)  # Exponential backoff: 1s, 2s, 4s
                    logger.info(f"Retrying in {backoff_time}s...")
                    time.sleep(backoff_time)
                else:
                    logger.error(f"All retries failed for {url} (Timeout)")
                    return None

            except requests.exceptions.ConnectionError as e:
                logger.warning(
                    f"Connection error on attempt {attempt}/{self.retry_attempts} for {url}: {e}"
                )
                if attempt < self.retry_attempts:
                    backoff_time = 2 ** (attempt - 1)
                    logger.info(f"Retrying in {backoff_time}s...")
                    time.sleep(backoff_time)
                else:
                    logger.error(f"All retries failed for {url} (Connection Error)")
                    return None

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error for {url}: {e}")
                return None

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}/{self.retry_attempts} for {url}: {e}")
                if attempt < self.retry_attempts:
                    backoff_time = 2 ** (attempt - 1)
                    logger.info(f"Retrying in {backoff_time}s...")
                    time.sleep(backoff_time)
                else:
                    logger.error(f"All retries failed for {url}")
                    return None

        return None

    def get_with_retry(self, url: str) -> Optional[str]:
        """
        Perform GET request and return text content

        Args:
            url: URL to fetch

        Returns:
            Response text if successful, None if failed
        """
        response = self.get(url)
        if response:
            return response.text
        return None

    def close(self) -> None:
        """
        Close the session
        """
        self.session.close()
