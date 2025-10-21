"""
Hash computation utilities for content change detection
"""

import hashlib


def compute_hash(html: str) -> str:
    """
    Compute MD5 hash of HTML content for change detection

    Args:
        html: HTML content string

    Returns:
        Hash string in format "md5:<hexdigest>"

    Examples:
        >>> compute_hash("<html><body>test</body></html>")
        'md5:9d3d9d...'
    """
    # Encode to UTF-8 bytes for consistent hashing
    html_bytes = html.encode("utf-8")

    # Compute MD5 hash
    md5_hash = hashlib.md5(html_bytes)

    # Return in specified format
    return f"md5:{md5_hash.hexdigest()}"
