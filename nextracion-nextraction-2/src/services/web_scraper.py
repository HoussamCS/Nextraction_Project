from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin

class WebScraper:
    def __init__(self, allowed_domains, max_depth):
        self.allowed_domains = allowed_domains
        self.max_depth = max_depth

    def is_allowed_domain(self, url):
        domain = urlparse(url).netloc
        return any(domain.endswith(allowed_domain) for allowed_domain in self.allowed_domains)

    def scrape(self, url, depth=0):
        if depth > self.max_depth or not self.is_allowed_domain(url):
            return []

        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return self.clean_html(soup)
        except requests.RequestException:
            return []

    def clean_html(self, soup):
        for script in soup(["script", "style"]):
            script.decompose()
        return ' '.join(soup.stripped_strings)

    def crawl(self, start_url):
        return self.scrape(start_url)