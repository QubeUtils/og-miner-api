import pytest
from app.services.parser import parser_service

def test_parser_title_extraction():
    html = """
    <html>
        <head>
            <meta property="og:title" content="OG Title">
            <title>Page Title</title>
        </head>
        <body></body>
    </html>
    """
    metadata = parser_service.parse(html, "http://example.com")
    assert metadata["title"] == "OG Title"

def test_parser_fallback_title():
    html = """
    <html>
        <head>
            <title>Page Title</title>
        </head>
        <body></body>
    </html>
    """
    metadata = parser_service.parse(html, "http://example.com")
    assert metadata["title"] == "Page Title"
