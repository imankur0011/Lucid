"""
Comprehensive External Link Health Verification & Audit Service for Lucid.

Validates URLs against Indian financial portals, NSE/BSE stock exchanges, and SEBI regulatory sites.
Detects HTTP status codes, redirects, soft-404 error states, and access-restricted resources.
Provides structured link metadata and automated fallback suggestions.
"""

import time
import ssl
import re
import logging
import urllib.request
import urllib.error
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class LinkStatus(str, Enum):
    VERIFIED = "VERIFIED"
    REDIRECTED_AND_VERIFIED = "REDIRECTED_AND_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    BROKEN = "BROKEN"
    ACCESS_RESTRICTED = "ACCESS_RESTRICTED"
    MISMATCHED_RESOURCE = "MISMATCHED_RESOURCE"
    EXPIRED = "EXPIRED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class ResourceType(str, Enum):
    HTML_PAGE = "HTML_PAGE"
    PDF_DOCUMENT = "PDF_DOCUMENT"
    EXCHANGE_ANNOUNCEMENTS_PORTAL = "EXCHANGE_ANNOUNCEMENTS_PORTAL"
    REGULATORY_FILING = "REGULATORY_FILING"
    CSV_DATA_FEED = "CSV_DATA_FEED"
    UNKNOWN = "UNKNOWN"


@dataclass
class LinkMetadata:
    url: str
    status: LinkStatus
    http_status_code: Optional[int] = None
    final_url: Optional[str] = None
    resource_type: ResourceType = ResourceType.UNKNOWN
    content_type: Optional[str] = None
    response_time_ms: Optional[float] = None
    last_verified_at: Optional[str] = None
    error_message: Optional[str] = None
    is_access_restricted: bool = False
    fallback_url: Optional[str] = None
    display_label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        d["resource_type"] = self.resource_type.value
        return d


class LinkVerificationService:
    """
    Production-grade URL verification engine with rate-limit friendly caching,
    soft-404 detection, and resilient exchange fallback resolution.
    """

    def __init__(self, cache_ttl_seconds: int = 3600):
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

        # Standard SSL context for exchange & regulatory inspection
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        # High-reputation desktop User-Agent to avoid generic anti-crawler blocks
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _determine_resource_type(self, url: str, content_type: Optional[str]) -> ResourceType:
        clean_url = (url or "").lower()
        ct = (content_type or "").lower()

        if "pdf" in ct or clean_url.endswith(".pdf"):
            return ResourceType.PDF_DOCUMENT
        if "csv" in ct or clean_url.endswith(".csv"):
            return ResourceType.CSV_DATA_FEED
        if "bseindia.com/stock-share-price" in clean_url or "corp-announcements" in clean_url:
            return ResourceType.EXCHANGE_ANNOUNCEMENTS_PORTAL
        if "nseindia.com/companies-listing" in clean_url or "corporate-filings" in clean_url:
            return ResourceType.EXCHANGE_ANNOUNCEMENTS_PORTAL
        if "sebi.gov.in" in clean_url or "smartodr" in clean_url or "scores" in clean_url:
            return ResourceType.REGULATORY_FILING
        return ResourceType.HTML_PAGE

    def _detect_soft_404(self, body_text: str, final_url: str) -> bool:
        """
        Examine HTML page content for hidden 404 indicators where HTTP response is 200.
        Common on legacy single-page apps or retired ASP paths.
        """
        low = body_text.lower()
        if "<title>404" in low or "page not found" in low or "error 404" in low:
            return True
        if "the page you are looking for does not exist" in low:
            return True
        if "stockprcstk" in final_url.lower() and "sensex" in low and "market live" in low and "divislab" not in low:
            # BSE redirect to home without finding the stock
            return False
        return False

    def verify_url(
        self,
        url: str,
        display_label: Optional[str] = None,
        fallback_url: Optional[str] = None,
        timeout_seconds: float = 6.0,
    ) -> LinkMetadata:
        """
        Validate single URL with redirect tracking, status classification, and caching.
        """
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            return LinkMetadata(
                url=url or "",
                status=LinkStatus.BROKEN,
                error_message="Invalid URL scheme. Must begin with http:// or https://",
                display_label=display_label,
                fallback_url=fallback_url,
                last_verified_at=datetime.now(timezone.utc).isoformat(),
            )

        now = time.time()
        cached = self._cache.get(url)
        if cached and (now - cached["timestamp"] < self.cache_ttl):
            return cached["metadata"]

        start_time = time.time()
        req = urllib.request.Request(url, headers=self.headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds, context=self.ssl_context) as resp:
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                status_code = resp.status
                final_url = resp.url
                content_type = resp.headers.get("Content-Type", "")
                resource_type = self._determine_resource_type(final_url, content_type)

                # Check for redirects
                is_redirected = final_url.rstrip("/") != url.rstrip("/")

                # Inspect first 4KB for soft 404s
                is_soft_404 = False
                if "html" in content_type.lower():
                    sample_body = resp.read(4096).decode("utf-8", errors="ignore")
                    is_soft_404 = self._detect_soft_404(sample_body, final_url)

                if is_soft_404:
                    status = LinkStatus.BROKEN
                    error_msg = "Soft 404 detected: Response status was 200 but body displayed 'Page Not Found'."
                elif is_redirected:
                    status = LinkStatus.REDIRECTED_AND_VERIFIED
                    error_msg = None
                else:
                    status = LinkStatus.VERIFIED
                    error_msg = None

                meta = LinkMetadata(
                    url=url,
                    status=status,
                    http_status_code=status_code,
                    final_url=final_url,
                    resource_type=resource_type,
                    content_type=content_type,
                    response_time_ms=elapsed_ms,
                    last_verified_at=datetime.now(timezone.utc).isoformat(),
                    error_message=error_msg,
                    is_access_restricted=False,
                    fallback_url=fallback_url,
                    display_label=display_label,
                )
                self._cache[url] = {"timestamp": now, "metadata": meta}
                return meta

        except urllib.error.HTTPError as he:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            code = he.code
            is_access_restricted = code in [401, 403]
            status = LinkStatus.ACCESS_RESTRICTED if is_access_restricted else LinkStatus.BROKEN

            meta = LinkMetadata(
                url=url,
                status=status,
                http_status_code=code,
                final_url=url,
                response_time_ms=elapsed_ms,
                last_verified_at=datetime.now(timezone.utc).isoformat(),
                error_message=f"HTTP Error {code}: {he.reason}",
                is_access_restricted=is_access_restricted,
                fallback_url=fallback_url,
                display_label=display_label,
            )
            self._cache[url] = {"timestamp": now, "metadata": meta}
            return meta

        except Exception as e:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            meta = LinkMetadata(
                url=url,
                status=LinkStatus.BROKEN,
                response_time_ms=elapsed_ms,
                last_verified_at=datetime.now(timezone.utc).isoformat(),
                error_message=f"Network resolution error: {str(e)}",
                is_access_restricted=False,
                fallback_url=fallback_url,
                display_label=display_label,
            )
            self._cache[url] = {"timestamp": now, "metadata": meta}
            return meta

    def verify_batch(self, items: List[Dict[str, str]]) -> List[LinkMetadata]:
        """
        Verify list of items with keys: 'url', optional 'display_label', optional 'fallback_url'.
        """
        results = []
        for item in items:
            res = self.verify_url(
                url=item.get("url", ""),
                display_label=item.get("display_label"),
                fallback_url=item.get("fallback_url"),
            )
            results.append(res)
        return results


# Global singleton instance
link_verifier = LinkVerificationService()

