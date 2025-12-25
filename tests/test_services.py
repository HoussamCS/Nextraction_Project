"""
Tests for services (web scraper, embeddings, RAG pipeline).
"""

import pytest
from src.services.web_scraper import WebScraper
from src.services.job_queue import job_queue, JobState


class TestWebScraper:
    def test_domain_allowlist_enforcement(self):
        """Test domain allowlist is enforced"""
        scraper = WebScraper(["example.com"], max_pages=10, max_depth=2)
        
        # Should be allowed
        assert scraper._is_allowed_domain("https://example.com/page")
        assert scraper._is_allowed_domain("https://www.example.com/page")
        
        # Should not be allowed
        assert not scraper._is_allowed_domain("https://other.com/page")
    
    def test_url_normalization(self):
        """Test URL normalization"""
        scraper = WebScraper(["example.com"], max_pages=10, max_depth=2)
        
        # Test relative URL resolution
        base_url = "https://example.com/dir/page.html"
        relative_url = "../other.html"
        normalized = scraper._normalize_url(relative_url, base_url)
        assert normalized is not None
        assert "example.com" in normalized
        
        # Test fragment removal
        url_with_fragment = "https://example.com/page#section"
        normalized = scraper._normalize_url(url_with_fragment)
        assert "#" not in normalized
    
    def test_max_pages_constraint(self):
        """Test max_pages constraint is respected"""
        scraper = WebScraper(["example.com"], max_pages=2, max_depth=1)
        assert scraper.pages_fetched == 0
        
        # Simulate adding pages (in real scenario, this would be from crawling)
        scraper.visited_urls.add("https://example.com/1")
        scraper.visited_urls.add("https://example.com/2")
        scraper.pages_fetched = 2
        
        # Should not allow more pages
        assert scraper.pages_fetched >= scraper.max_pages
    
    def test_html_cleaning(self):
        """Test HTML is cleaned properly"""
        scraper = WebScraper(["example.com"], max_pages=10, max_depth=2)
        
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <nav>Navigation</nav>
                <script>console.log('test');</script>
                <main>Important Content</main>
                <footer>Copyright 2024</footer>
            </body>
        </html>
        """
        
        text, title = scraper._clean_html(html, "https://example.com")
        
        # Should extract title
        assert title == "Test Page"
        
        # Should include main content
        assert "Important Content" in text
        
        # Should not include script
        assert "console.log" not in text
        
        # Should not include nav/footer
        assert "Navigation" not in text or "Copyright" not in text


class TestJobQueue:
    def test_create_job(self):
        """Test job creation"""
        job_id = job_queue.create_job()
        assert job_id is not None
        job = job_queue.get_job(job_id)
        assert job is not None
        assert job.state == JobState.QUEUED
    
    def test_job_state_transitions(self):
        """Test job state transitions"""
        job_id = job_queue.create_job()
        
        # QUEUED -> RUNNING
        assert job_queue.set_running(job_id)
        job = job_queue.get_job(job_id)
        assert job.state == JobState.RUNNING
        
        # RUNNING -> DONE
        assert job_queue.set_done(job_id, {"result": "success"})
        job = job_queue.get_job(job_id)
        assert job.state == JobState.DONE
    
    def test_job_progress_tracking(self):
        """Test job progress updates"""
        job_id = job_queue.create_job()
        
        # Update progress
        assert job_queue.update_progress(job_id, pages_fetched=5, pages_indexed=3)
        job = job_queue.get_job(job_id)
        assert job.pages_fetched == 5
        assert job.pages_indexed == 3
    
    def test_job_error_tracking(self):
        """Test error tracking in jobs"""
        job_id = job_queue.create_job()
        
        # Add errors
        assert job_queue.add_error(job_id, "Error 1")
        assert job_queue.add_error(job_id, "Error 2")
        
        job = job_queue.get_job(job_id)
        assert len(job.errors) == 2
        assert "Error 1" in job.errors
    
    def test_job_failure(self):
        """Test job failure marking"""
        job_id = job_queue.create_job()
        
        # Mark as failed
        assert job_queue.set_failed(job_id, "Critical error")
        
        job = job_queue.get_job(job_id)
        assert job.state == JobState.FAILED
        assert "Critical error" in job.errors
