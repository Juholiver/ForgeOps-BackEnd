import ipaddress
import socket
from urllib.parse import urlparse


class SSRFProtection:
    BLOCKED_HOSTNAMES = {"localhost", "metadata.google.internal", "instance-data"}

    @staticmethod
    def is_safe_url(url: str) -> tuple[bool, str]:
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname

            if not hostname:
                return False, "Invalid URL"

            if hostname.lower() in SSRFProtection.BLOCKED_HOSTNAMES:
                return False, f"Hostname {hostname} is not allowed"

            try:
                ip = ipaddress.ip_address(hostname)
            except ValueError:
                try:
                    ip = ipaddress.ip_address(socket.gethostbyname(hostname))
                except socket.gaierror:
                    return False, f"Cannot resolve hostname {hostname}"

            if ip.is_loopback:
                return False, "Loopback addresses are not allowed"
            if ip.is_link_local:
                return False, "Link-local addresses are not allowed"
            if ip.is_private:
                return False, "Private IP addresses are not allowed"
            if ip.is_reserved:
                return False, "Reserved IP addresses are not allowed"
            if ip.is_multicast:
                return False, "Multicast addresses are not allowed"

            return True, ""
        except Exception as e:
            return False, f"URL validation error: {str(e)}"
