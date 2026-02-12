import pytest
from app.services.parser import parser_service
import json

def test_parser_json_ld():
    html = """
    <html>
        <head>
            <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Recipe",
                    "name": "Grandma's Pie"
                }
            </script>
        </head>
        <body></body>
    </html>
    """
    metadata = parser_service.parse(html, "http://example.com")
    assert metadata["json_ld"]
    # extracted structure depends on extruct version, but it should contain our list
    # extruct returns a list of dictionaries usually
    assert isinstance(metadata["json_ld"], list)
    assert any(item.get("name") == "Grandma's Pie" for item in metadata["json_ld"])

def test_parser_canonical_url():
    html = """
    <html>
        <head>
            <link rel="canonical" href="https://example.com/canonical-page" />
        </head>
        <body></body>
    </html>
    """
    metadata = parser_service.parse(html, "http://example.com/duplicate")
    assert metadata["canonical_url"] == "https://example.com/canonical-page"

def test_parser_oembed_discovery():
    html = """
    <html>
        <head>
            <link rel="alternate" type="application/json+oembed" href="https://example.com/oembed?url=..." />
        </head>
        <body></body>
    </html>
    """
    metadata = parser_service.parse(html, "http://example.com")
    assert metadata["oembed_url"] == "https://example.com/oembed?url=..."
