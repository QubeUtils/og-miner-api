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

def validate_proxy_url(proxy_url: str) -> None:
    """
    Validates a user-provided proxy URL.
    Ensures it has a scheme, host, and port, and does not point to a local network.
    """
    try:
        parsed = urlparse(proxy_url)
        if parsed.scheme not in ("http", "https", "socks4", "socks5"):
             raise ValueError("Proxy URL must be http, https, socks4, or socks5")
        
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("Invalid Proxy URL: No hostname found")
            
        # Resolve and check for SSRF
        # We reuse the logic from validate_url but wrap it for context
        try:
             # This re-implements the resolution and checking logic against BLOCKED_NETWORKS
             # We could refactor validate_url to be more generic, but for now copying the IP check is safer/clearer
             ip_str = socket.gethostbyname(hostname)
             ip_addr = ipaddress.ip_address(ip_str)
             
             for network in BLOCKED_NETWORKS:
                if ip_addr in network:
                    logger.warning("proxy_ssrf_blocked", proxy=proxy_url, resolved_ip=ip_str)
                    raise ValueError(f"Proxy host {hostname} resolves to broken/private IP {ip_str}")
                    
        except socket.gaierror:
             # For a proxy, if it doesn't resolve, it's definitely broken
             raise ValueError(f"Could not resolve proxy hostname: {hostname}")
             
    except Exception as e:
         if isinstance(e, ValueError):
            raise e
         logger.warning("invalid_user_proxy", proxy=proxy_url, error=str(e))
         raise ValueError(f"Invalid proxy URL: {str(e)}")
