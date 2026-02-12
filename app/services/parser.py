import extruct
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class ParserService:
    def parse(self, html: str, url: str) -> dict:
        soup = BeautifulSoup(html, "lxml")
        
        # JSON-LD Extraction
        try:
            # extruct expects bytes or robust html string. 
            # It extracts all microdata, json-ld, rdfa, etc. We filter for json-ld.
            extracted_data = extruct.extract(html, base_url=url, uniform=True)
            json_ld = extracted_data.get('json-ld', [])
        except Exception:
            json_ld = []

        metadata = {
            "title": self._get_title(soup),
            "description": self._get_description(soup),
            "image": self._get_image(soup, url),
            "favicon": self._get_favicon(soup, url),
            "author": self._get_author(soup),
            "site_name": self._get_site_name(soup),
            "canonical_url": self._get_canonical_url(soup, url),
            "json_ld": json_ld,
            "oembed_url": self._get_oembed_discovery_url(soup, url) # Internal use for fetcher
        }
        
        return metadata

    def _get_title(self, soup: BeautifulSoup) -> str | None:
        # og:title -> twitter:title -> <title>
        og = soup.find("meta", property="og:title")
        if og: return og.get("content")
        
        twitter = soup.find("meta", attrs={"name": "twitter:title"})
        if twitter: return twitter.get("content")
        
        title = soup.find("title")
        if title: return title.string
        return None

    def _get_description(self, soup: BeautifulSoup) -> str | None:
        # og:description -> twitter:description -> <meta name="description">
        og = soup.find("meta", property="og:description")
        if og: return og.get("content")
        
        twitter = soup.find("meta", attrs={"name": "twitter:description"})
        if twitter: return twitter.get("content")
        
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc: return meta_desc.get("content")
        return None

    def _get_image(self, soup: BeautifulSoup, base_url: str) -> str | None:
        # og:image -> twitter:image -> first <img> > 200px width (complex to check width without fetching, skipping size check for now or approximate)
        image_url = None
        
        og_image = soup.find("meta", property="og:image")
        if og_image:
            image_url = og_image.get("content")
        
        if not image_url:
            twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
            if twitter_image:
                image_url = twitter_image.get("content")
        
        if not image_url:
            # Fallback to first image (naive)
            img = soup.find("img")
            if img:
                image_url = img.get("src")
        
        if image_url:
            return urljoin(base_url, image_url)
        return None

    def _get_favicon(self, soup: BeautifulSoup, base_url: str) -> str:
        # <link rel="icon"> -> default /favicon.ico
        icon_link = soup.find("link", rel=lambda x: x and "icon" in x.lower().split())
        if icon_link:
            return urljoin(base_url, icon_link.get("href"))
        return urljoin(base_url, "/favicon.ico")

    def _get_author(self, soup: BeautifulSoup) -> str | None:
         author = soup.find("meta", attrs={"name": "author"})
         if author: return author.get("content")
         
         article_author = soup.find("meta", property="article:author")
         if article_author: return article_author.get("content")
         return None

    def _get_site_name(self, soup: BeautifulSoup) -> str | None:
        return (
            soup.find("meta", property="og:site_name")
        ).get("content", None) if soup.find("meta", property="og:site_name") else None

    def _get_canonical_url(self, soup: BeautifulSoup, base_url: str) -> str | None:
        canonical = soup.find("link", rel="canonical")
        if canonical:
            return urljoin(base_url, canonical.get("href"))
        return base_url # Default to logical base if no canonical tag? Or None? Standard is to return None or the URL itself. Let's return None implies "same as requested" or let caller decide. Actually returning None is safer. But often strict parsers prefer the fetched URL if no canonical. Let's return None for now.
        
    def _get_oembed_discovery_url(self, soup: BeautifulSoup, base_url: str) -> str | None:
        # <link rel="alternate" type="application/json+oembed" href="...">
        oembed_link = soup.find("link", type="application/json+oembed")
        if oembed_link:
            return urljoin(base_url, oembed_link.get("href"))
        return None

parser_service = ParserService()
