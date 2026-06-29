"""Tunnel manager — Cloudflare Tunnel integration for public access."""

from __future__ import annotations

import asyncio
import logging
import subprocess
import re
from typing import Optional

from forge.core.config import settings

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')


class TunnelManager:
    """Manages Cloudflare Tunnel for public HTTPS access to the forge daemon."""

    def __init__(self):
        self._process: Optional[asyncio.subprocess.Process] = None
        self._public_url: Optional[str] = None

    async def start(self, local_url: str = "http://127.0.0.1:8765") -> str:
        """Start a Cloudflare tunnel and return the public URL."""
        if self._process is not None:
            raise RuntimeError("Tunnel is already running")

        bin_path = settings.cloudflared_bin
        cmd = [bin_path, "tunnel", "--url", local_url, "--no-autoupdate"]

        logger.info("Starting tunnel: %s", " ".join(cmd))

        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        # Wait for the trycloudflare URL to appear in stdout
        deadline = asyncio.get_event_loop().time() + 30
        while asyncio.get_event_loop().time() < deadline:
            line = await asyncio.wait_for(self._process.stdout.readline(), timeout=30)
            text = line.decode("utf-8", errors="replace")
            logger.debug("cloudflared: %s", text.strip())
            match = URL_PATTERN.search(text)
            if match:
                self._public_url = match.group(0)
                logger.info("Tunnel established: %s", self._public_url)
                return self._public_url

        raise RuntimeError("Tunnel failed to start within 30 seconds")

    async def stop(self):
        """Stop the tunnel."""
        if self._process:
            try:
                self._process.kill()
                await self._process.wait()
            except Exception:
                pass
            self._process = None
            self._public_url = None
            logger.info("Tunnel stopped")

    @property
    def public_url(self) -> Optional[str]:
        return self._public_url

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.returncode is None


# Global instance
tunnel_manager = TunnelManager()
