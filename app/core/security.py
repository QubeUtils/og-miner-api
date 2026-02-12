import socket
import ipaddress
from urllib.parse import urlparse
from app.utils.logger import logger

# Private IP ranges (RFC 1918 + Localhost)
BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
]

def validate_url(url: str) -> None:
    """
    Validates that the URL does not point to a local/private IP address (SSRF protection).
    Raises ValueError if validation fails.
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("Invalid URL: No hostname found")
            
        # Resolve hostname to IP
        try:
            ip_str = socket.gethostbyname(hostname)
        except socket.gaierror:
            # If DNS resolution fails, it might be an invalid domain, but we can't SSRF it if we can't reach it.
            # However, for our fetcher, we should probably fail here.
            raise ValueError(f"Could not resolve hostname: {hostname}")
            
        ip_addr = ipaddress.ip_address(ip_str)
        
        # Check against blocked networks
        for network in BLOCKED_NETWORKS:
            if ip_addr in network:
                logger.warning("ssrf_attempt_blocked", url=url, resolved_ip=ip_str)
                raise ValueError(f"Access to local resource {hostname} ({ip_str}) is forbidden")
                
    except Exception as e:
        # Re-raise known ValueErrors, wrap others
        if isinstance(e, ValueError):
            raise e
        logger.error("url_validation_error", url=url, error=str(e))
        raise ValueError(f"URL validation failed: {str(e)}")
