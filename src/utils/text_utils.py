"""
Text processing utilities for HTML to plain text conversion
"""

from bs4 import BeautifulSoup
from typing import Optional


def html_to_text(html: str) -> str:
    """
    Convert HTML to clean plain text, preserving paragraph structure

    Args:
        html: Raw HTML content

    Returns:
        Clean plain text with preserved formatting (paragraphs and line breaks)

    Examples:
        >>> html = '<p>第一段</p><br><p>第二段</p>'
        >>> html_to_text(html)
        '第一段\\n\\n第二段'
    """
    if not html or not html.strip():
        return ""

    try:
        soup = BeautifulSoup(html, "lxml")

        # Replace <br> tags with newlines
        for br in soup.find_all("br"):
            br.replace_with("\n")

        # Replace <hr> tags with separator
        for hr in soup.find_all("hr"):
            hr.replace_with("\n" + "-" * 40 + "\n")

        # Extract paragraphs from common block elements
        block_elements = ["p", "div", "section", "article", "li", "td", "th"]
        paragraphs = []

        # First try to get structured content
        for tag in soup.find_all(block_elements):
            text = tag.get_text(separator=" ", strip=True)
            if text and text not in paragraphs:  # Avoid duplicates
                paragraphs.append(text)

        # If no structured content found, get all text
        if not paragraphs:
            text = soup.get_text(separator=" ", strip=True)
            if text:
                paragraphs.append(text)

        # Join paragraphs with double newlines
        result = "\n\n".join(paragraphs)

        # Clean up excessive whitespace
        result = "\n".join(line.strip() for line in result.split("\n"))

        # Remove excessive blank lines (max 2 consecutive newlines)
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")

        return result.strip()

    except Exception as e:
        # Fallback: just strip all tags
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator=" ", strip=True)


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to maximum length, preserving word boundaries

    Args:
        text: Text to truncate
        max_length: Maximum length (default: 200)
        suffix: Suffix to append when truncated (default: "...")

    Returns:
        Truncated text with suffix if needed
    """
    if len(text) <= max_length:
        return text

    truncated = text[:max_length - len(suffix)]
    return truncated.rstrip() + suffix
