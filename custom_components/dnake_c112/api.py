"""DNAKE C112 HTTP / RTSP istemcisi."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from urllib.parse import quote

import aiohttp

_LOGGER = logging.getLogger(__name__)

TIMEOUT = aiohttp.ClientTimeout(total=8)


class DnakeError(Exception):
    """C112 ile iletişim hatası."""


class DnakeAuthError(DnakeError):
    """Kullanıcı adı/şifre hatası."""


class DnakeC112:
    """C112 kapı paneli."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        username: str,
        password: str,
        rtsp_port: int,
        rtsp_path: str,
    ) -> None:
        self._session = session
        self.host = host.strip().removeprefix("http://").rstrip("/")
        self.username = username
        self._password = password
        # DNAKE CGI komutu şifrenin MD5'ini bekler (ör. 123456 -> E10ADC39...)
        self._password_md5 = hashlib.md5(password.encode()).hexdigest().upper()
        self.rtsp_port = rtsp_port
        self.rtsp_path = rtsp_path.lstrip("/")

    @property
    def rtsp_url(self) -> str:
        """Kimlik bilgili RTSP adresi."""
        user = quote(self.username, safe="")
        pwd = quote(self._password, safe="")
        return f"rtsp://{user}:{pwd}@{self.host}:{self.rtsp_port}/{self.rtsp_path}"

    @property
    def rtsp_url_redacted(self) -> str:
        """Loglarda kullanılacak şifresiz RTSP adresi."""
        return f"rtsp://{self.username}:***@{self.host}:{self.rtsp_port}/{self.rtsp_path}"

    async def async_check_reachable(self) -> None:
        """Panelin web arayüzüne ulaşılabiliyor mu? (kapıyı açmadan)"""
        try:
            async with self._session.get(
                f"http://{self.host}/", timeout=TIMEOUT, allow_redirects=True
            ) as resp:
                _LOGGER.debug("C112 %s yanıtı: HTTP %s", self.host, resp.status)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise DnakeError(f"{self.host} adresine ulaşılamadı: {err}") from err

    async def async_unlock(self, relay_index: int) -> None:
        """Röleyi tetikle (kapıyı aç)."""
        params = {
            "api": "unlock",
            "index": str(relay_index),
            "username": self.username,
            "password": self._password_md5,
        }
        url = f"http://{self.host}/cgi-bin/webapi.cgi"
        try:
            async with self._session.get(url, params=params, timeout=TIMEOUT) as resp:
                body = await resp.text(errors="ignore")
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise DnakeError(f"Kapı açma komutu gönderilemedi: {err}") from err

        _LOGGER.debug(
            "C112 unlock index=%s -> HTTP %s, yanıt: %s",
            relay_index,
            resp.status,
            body[:200],
        )
        if resp.status in (401, 403):
            raise DnakeAuthError("Kullanıcı adı veya şifre hatalı")
        if resp.status != 200:
            raise DnakeError(
                f"Kapı paneli HTTP {resp.status} döndü. Web arayüzünde "
                "'Open relay via HTTP' açık mı ve şifre doğru mu?"
            )
        # Not: C112'nin başarı yanıtının gövde biçimi belgelenmemiş; HTTP 200
        # başarı sayılır, gövde debug loguna yazılır.
