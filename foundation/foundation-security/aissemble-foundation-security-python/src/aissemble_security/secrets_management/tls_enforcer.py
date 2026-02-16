"""
STIG V-220634 / NIST SC-8: TLS 1.2+ Enforcement
Utilities to verify and enforce TLS configuration.
"""

import ssl
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

MINIMUM_TLS_VERSION = ssl.TLSVersion.TLSv1_2


class TLSEnforcer:
    """Enforces TLS 1.2+ for all network communications per STIG V-220634."""

    @staticmethod
    def create_secure_context(
        purpose: ssl.Purpose = ssl.Purpose.SERVER_AUTH,
        certfile: str = "",
        keyfile: str = "",
        cafile: str = "",
    ) -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT if purpose == ssl.Purpose.SERVER_AUTH else ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        context.set_ciphers(
            "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20"
        )
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        context.options |= ssl.OP_NO_COMPRESSION

        if certfile:
            context.load_cert_chain(certfile=certfile, keyfile=keyfile or None)
        if cafile:
            context.load_verify_locations(cafile=cafile)

        logger.info(
            "Secure TLS context created with minimum version TLS 1.2"
        )
        return context

    @staticmethod
    def verify_tls_version(hostname: str, port: int = 443) -> Tuple[bool, str]:
        try:
            context = ssl.create_default_context()
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            with context.wrap_socket(
                __import__("socket").create_connection((hostname, port), timeout=10),
                server_hostname=hostname,
            ) as ssock:
                version = ssock.version()
                if version and version in ("TLSv1.2", "TLSv1.3"):
                    return True, f"Connection uses {version}"
                return False, f"Insecure TLS version: {version}"
        except ssl.SSLError as e:
            return False, f"TLS verification failed: {e}"
        except Exception as e:
            return False, f"Connection failed: {e}"

    @staticmethod
    def check_url_uses_tls(url: str) -> Tuple[bool, str]:
        if not url.startswith("https://"):
            return False, "URL does not use HTTPS"
        return True, "URL uses HTTPS"
