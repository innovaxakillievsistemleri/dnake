"""DNAKE C112 kurulum ve seçenek akışı."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import webhook
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.network import NoURLAvailableError
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import DnakeC112, DnakeError
from .const import (
    CONF_LOCAL_ONLY,
    CONF_RING_DURATION,
    CONF_RTSP_PATH,
    CONF_RTSP_PORT,
    CONF_WEBHOOK_ID,
    DEFAULT_LOCAL_ONLY,
    DEFAULT_RING_DURATION,
    DEFAULT_RTSP_PATH,
    DEFAULT_RTSP_PORT,
    DEFAULT_USERNAME,
    DOMAIN,
    MODEL,
)

_LOGGER = logging.getLogger(__name__)

PORT_SELECTOR = NumberSelector(
    NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
)
PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


def _user_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Kurulum formu (önceki girişlerle doldurulur)."""
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Required(
                CONF_USERNAME, default=defaults.get(CONF_USERNAME, DEFAULT_USERNAME)
            ): str,
            vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
            vol.Required(
                CONF_RTSP_PORT, default=defaults.get(CONF_RTSP_PORT, DEFAULT_RTSP_PORT)
            ): PORT_SELECTOR,
            vol.Required(
                CONF_RTSP_PATH, default=defaults.get(CONF_RTSP_PATH, DEFAULT_RTSP_PATH)
            ): str,
        }
    )


def webhook_url(hass: HomeAssistant, webhook_id: str) -> str:
    """C112'ye girilecek zil adresi."""
    try:
        return webhook.async_generate_url(hass, webhook_id)
    except NoURLAvailableError:
        return f"http://<home-assistant-ip>:8123{webhook.async_generate_path(webhook_id)}"


class DnakeC112ConfigFlow(ConfigFlow, domain=DOMAIN):
    """C112 kurulum akışı."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Adres ve kimlik bilgilerini al."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_RTSP_PORT] = int(user_input[CONF_RTSP_PORT])
            api = DnakeC112(
                async_get_clientsession(self.hass),
                user_input[CONF_HOST],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input[CONF_RTSP_PORT],
                user_input[CONF_RTSP_PATH],
            )
            # Adresi normalleştir (http:// öneki, sondaki / vb.)
            user_input[CONF_HOST] = api.host

            await self.async_set_unique_id(api.host)
            self._abort_if_unique_id_configured()

            try:
                # Kimlik bilgisi kapıyı açmadan doğrulanamıyor; yalnız erişim
                # kontrol edilir.
                await api.async_check_reachable()
            except DnakeError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("C112 kurulumunda beklenmeyen hata")
                errors["base"] = "unknown"
            else:
                webhook_id = webhook.async_generate_id()
                return self.async_create_entry(
                    title=f"Innovax İnterkom {api.host}",
                    data={**user_input, CONF_WEBHOOK_ID: webhook_id},
                    description_placeholders={
                        "webhook_url": webhook_url(self.hass, webhook_id)
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(user_input or {}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> DnakeC112OptionsFlow:
        """Seçenek akışı."""
        return DnakeC112OptionsFlow()


class DnakeC112OptionsFlow(OptionsFlow):
    """Zil süresi ve webhook erişimi."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Seçenekleri düzenle."""
        if user_input is not None:
            user_input[CONF_RING_DURATION] = int(user_input[CONF_RING_DURATION])
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_RING_DURATION,
                    default=options.get(CONF_RING_DURATION, DEFAULT_RING_DURATION),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=600,
                        step=1,
                        unit_of_measurement="s",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_LOCAL_ONLY,
                    default=options.get(CONF_LOCAL_ONLY, DEFAULT_LOCAL_ONLY),
                ): bool,
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "webhook_url": webhook_url(
                    self.hass, self.config_entry.data[CONF_WEBHOOK_ID]
                )
            },
        )
