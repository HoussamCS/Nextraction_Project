from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin
from datetime import datetime
import hashlib
import logging
from typing import List, Dict, Tuple, Set
import time

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, domain_allowlist: List[str], max_pages: int, max_depth: int):
        self.domain_allowlist = domain_allowlist
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited_urls: Set[str] = set()
        self.pages_fetched = 0
        self.errors: List[str] = []
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.timeout = 10
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
    
    def _is_allowed_domain(self, url: str) -> bool:
        """Check if URL domain is in allowlist."""
        try:
            domain = urlparse(url).netloc
            # Remove www. prefix for comparison
            domain_clean = domain.replace("www.", "")
            
            for allowed in self.domain_allowlist:
                allowed_clean = allowed.replace("www.", "")
                # Check if allowed domain is a suffix of the URL domain (handles subdomains)
                # e.g., "wikipedia.org" matches "en.wikipedia.org"
                if domain_clean == allowed_clean or domain_clean.endswith("." + allowed_clean):
                    return True
            return False
        except Exception as e:
            logger.error(f"Domain check failed for {url}: {e}")
            return False
    
    def _normalize_url(self, url: str, base_url: str = None) -> str:
        """Normalize and resolve relative URLs."""
        try:
            if base_url and not url.startswith(("http://", "https://")):
                url = urljoin(base_url, url)
            # Remove fragments
            url = url.split("#")[0]
            return url.rstrip("/")
        except Exception as e:
            logger.error(f"URL normalization failed for {url}: {e}")
            return None
    
    def _clean_html(self, html: str, url: str) -> Tuple[str, str]:
        """
        Convert HTML to clean text. Remove navigation, footer, boilerplate.
        Returns (cleaned_text, page_title)
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove script, style, nav, footer, noscript, meta, link
            for element in soup(["script", "style", "nav", "footer", "noscript", "meta", "link"]):
                element.decompose()
            
            # Remove common boilerplate classes
            for element in soup.find_all(class_=lambda x: x and any(
                cls in (x or "").lower() for cls in ["sidebar", "advertisement", "cookie", "consent", "popup", "modal"]
            )):
                element.decompose()
            
            # Extract title
            title = "Unknown"
            if soup.title:
                title = soup.title.string or "Unknown"
            elif soup.find("h1"):
                title = soup.find("h1").get_text(strip=True)
            
            # Extract main content
            text = soup.get_text(separator=" ", strip=True)
            
            # Collapse whitespace
            text = " ".join(text.split())
            
            return text, title
        except Exception as e:
            logger.error(f"HTML cleaning failed for {url}: {e}")
            return "", "Unknown"
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract all links from HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            links = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                normalized = self._normalize_url(href, base_url)
                if normalized and self._is_allowed_domain(normalized):
                    links.append(normalized)
            return links
        except Exception as e:
            logger.error(f"Link extraction failed for {base_url}: {e}")
            return []
    
    def _fetch_page(self, url: str) -> Tuple[str, bool]:
        """
        Fetch a single page. Returns (html_content, success).
        Implements timeout and limited retries.
        """
        if self.pages_fetched >= self.max_pages:
            return "", False
        
        if url in self.visited_urls:
            return "", False
        
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Check if response is HTML
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                logger.warning(f"Non-HTML content type for {url}: {content_type}")
                return "", False
            
            self.visited_urls.add(url)
            self.pages_fetched += 1
            logger.info(f"Fetched page {self.pages_fetched}/{self.max_pages}: {url}")
            
            time.sleep(0.5)  # Polite crawling delay
            return response.text, True
            
        except requests.Timeout:
            error_msg = f"Timeout fetching {url}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.visited_urls.add(url)
            return "", False
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                error_msg = f"Access denied (403) for {url} - server rejected request"
                logger.warning(error_msg)
            else:
                error_msg = f"HTTP error {e.response.status_code} for {url}"
                logger.error(error_msg)
            self.errors.append(error_msg)
            self.visited_urls.add(url)
            return "", False
        except requests.exceptions.ConnectionError as e:
            if "Name or service not known" in str(e) or "getaddrinfo failed" in str(e) or "nodename nor servname provided" in str(e):
                error_msg = f"DNS resolution failed for {url} - domain may not exist or be unreachable"
            else:
                error_msg = f"Connection failed for {url}: {str(e)}"
            logger.warning(error_msg)
            self.visited_urls.add(url)
            return "", False
        except requests.RequestException as e:
            error_msg = f"Request failed for {url}: {str(e)}"
            logger.error(error_msg)
            self.visited_urls.add(url)
            return "", False
        except Exception as e:
            error_msg = f"Unexpected error fetching {url}: {str(e)}"
            logger.error(error_msg)
            self.visited_urls.add(url)
            return "", False
    
    def crawl(self, seed_urls: List[str]) -> List[Dict]:
        """
        Crawl starting from seed URLs, respecting domain allowlist, max_depth, and max_pages.
        Returns list of page data (url, title, content, timestamp, chunk_id).
        """
        pages_data = []
        to_visit = [(url, 0) for url in seed_urls]  # (url, depth)
        logger.info(f"Starting crawl with {len(seed_urls)} seed URLs, max_depth={self.max_depth}, max_pages={self.max_pages}")
        logger.info(f"Allowed domains: {self.domain_allowlist}")
        
        while to_visit and self.pages_fetched < self.max_pages:
            url, depth = to_visit.pop(0)
            logger.info(f"Processing URL (depth {depth}): {url}")
            
            # Skip if depth exceeded or already visited
            if depth > self.max_depth:
                logger.info(f"Skipping {url} - depth {depth} exceeds max {self.max_depth}")
                continue
            
            if url in self.visited_urls:
                logger.info(f"Skipping {url} - already visited")
                continue
            
            # Skip if domain not allowed
            if not self._is_allowed_domain(url):
                logger.warning(f"Skipping {url} - domain not in allowlist")
                continue
            
            # Fetch page
            html, success = self._fetch_page(url)
            if not success:
                continue
            
            # Clean HTML and extract content
            text, title = self._clean_html(html, url)
            
            # Reject if page has too little text (less than 100 chars)
            if len(text) < 100:
                logger.warning(f"Page too small, skipping: {url}")
                continue
            
            # Generate stable chunk ID
            chunk_id = hashlib.md5(f"{url}:page".encode()).hexdigest()[:12]
            
            # Store page data
            page_data = {
                "url": url,
                "title": title,
                "content": text,
                "timestamp": datetime.utcnow().isoformat(),
                "chunk_id": chunk_id
            }
            pages_data.append(page_data)
            logger.info(f"Indexed page: {url}")
            
            # Extract and queue links for next depth level
            if depth < self.max_depth and self.pages_fetched < self.max_pages:
                links = self._extract_links(html, url)
                for link in links:
                    if link not in self.visited_urls and link not in [u for u, _ in to_visit]:
                        to_visit.append((link, depth + 1))
        
        logger.info(f"Crawl complete: {len(pages_data)} pages indexed, {len(self.errors)} errors")
        return pages_data