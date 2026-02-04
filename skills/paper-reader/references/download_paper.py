#!/usr/bin/env python3
"""
Paper PDF Downloader

Downloads research papers from URLs (arxiv, OpenReview, etc.) to local files.
Supports automatic URL normalization for common paper repositories.

Usage:
    python download_paper.py <url> [output_path]
    
Examples:
    python download_paper.py https://arxiv.org/abs/2505.22596
    python download_paper.py https://arxiv.org/pdf/2505.22596 ./papers/
    python download_paper.py https://openreview.net/pdf?id=xxx paper.pdf
"""

import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple


def normalize_arxiv_url(url: str) -> str:
    """
    Convert arxiv URLs to direct PDF download links.
    
    Handles:
        - https://arxiv.org/abs/2505.22596 -> https://arxiv.org/pdf/2505.22596.pdf
        - https://arxiv.org/pdf/2505.22596 -> https://arxiv.org/pdf/2505.22596.pdf
        - https://arxiv.org/pdf/2505.22596.pdf -> unchanged
    """
    # Extract arxiv ID from various URL formats
    patterns = [
        r'arxiv\.org/abs/(\d+\.\d+)',      # abs page
        r'arxiv\.org/pdf/(\d+\.\d+)',      # pdf without extension
        r'arxiv\.org/pdf/(\d+\.\d+)\.pdf', # pdf with extension
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            arxiv_id = match.group(1)
            return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    return url


def normalize_url(url: str) -> str:
    """
    Normalize paper URL to direct PDF download link.
    Supports: arxiv, OpenReview, and direct PDF links.
    """
    url = url.strip()
    
    # Handle arxiv
    if 'arxiv.org' in url:
        return normalize_arxiv_url(url)
    
    # Handle OpenReview (already direct PDF link format)
    if 'openreview.net/pdf' in url:
        return url
    
    # For other URLs, assume direct PDF link
    return url


def extract_filename_from_url(url: str) -> str:
    """Extract a reasonable filename from the URL."""
    
    # For arxiv, use the paper ID
    arxiv_match = re.search(r'arxiv\.org/pdf/(\d+\.\d+)', url)
    if arxiv_match:
        return f"arxiv_{arxiv_match.group(1)}.pdf"
    
    # For OpenReview, use the paper ID
    openreview_match = re.search(r'openreview\.net/pdf\?id=(\w+)', url)
    if openreview_match:
        return f"openreview_{openreview_match.group(1)}.pdf"
    
    # Fallback: use last part of URL path
    path = url.split('?')[0].split('/')[-1]
    if path and not path.endswith('.pdf'):
        path = f"{path}.pdf"
    
    return path or "paper.pdf"


def download_pdf(
    url: str,
    output_path: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 2.0,
    timeout: int = 30
) -> Tuple[bool, str]:
    """
    Download a PDF from URL with retry mechanism.
    
    Args:
        url: Paper URL (arxiv, OpenReview, or direct PDF link)
        output_path: Output file path or directory. If None, uses current directory.
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        timeout: Request timeout in seconds
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Normalize URL
    pdf_url = normalize_url(url)
    
    # Determine output path
    if output_path is None:
        output_file = Path.cwd() / extract_filename_from_url(pdf_url)
    elif os.path.isdir(output_path):
        output_file = Path(output_path) / extract_filename_from_url(pdf_url)
    else:
        output_file = Path(output_path)
    
    # Ensure parent directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Set up request headers (some sites block default urllib user-agent)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[Attempt {attempt}/{max_retries}] Downloading: {pdf_url}")
            
            request = urllib.request.Request(pdf_url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=timeout) as response:
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                if 'application/pdf' not in content_type and 'octet-stream' not in content_type:
                    # Some servers don't set correct content-type, check first bytes
                    content = response.read()
                    if not content.startswith(b'%PDF'):
                        return False, f"URL does not point to a PDF file (Content-Type: {content_type})"
                else:
                    content = response.read()
                
                # Verify PDF signature
                if not content.startswith(b'%PDF'):
                    return False, "Downloaded content is not a valid PDF file"
                
                # Save to file
                with open(output_file, 'wb') as f:
                    f.write(content)
                
                file_size = len(content) / 1024  # KB
                return True, f"Successfully downloaded to: {output_file} ({file_size:.1f} KB)"
        
        except urllib.error.HTTPError as e:
            last_error = f"HTTP Error {e.code}: {e.reason}"
            if e.code == 404:
                return False, f"Paper not found (404): {pdf_url}"
            elif e.code == 403:
                return False, f"Access denied (403): {pdf_url}"
        
        except urllib.error.URLError as e:
            last_error = f"URL Error: {e.reason}"
        
        except TimeoutError:
            last_error = "Request timed out"
        
        except Exception as e:
            last_error = f"Unexpected error: {str(e)}"
        
        # Wait before retry
        if attempt < max_retries:
            print(f"  Retrying in {retry_delay}s... (Error: {last_error})")
            time.sleep(retry_delay)
    
    return False, f"Failed after {max_retries} attempts. Last error: {last_error}"


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nError: Please provide a URL")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    success, message = download_pdf(url, output_path)
    print(message)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
