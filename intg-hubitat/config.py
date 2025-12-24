"""Configuration management for Hubitat integration."""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_LOG = logging.getLogger(__name__)


@dataclass
class HubitatConfig:
    """Hubitat hub configuration."""

    hub_address: str
    maker_api_id: str
    access_token: str


class ConfigurationManager:
    """Manages integration configuration."""

    def __init__(self, config_dir: Path | None = None):
        """
        Initialize configuration manager.

        Args:
            config_dir: Configuration directory path
        """
        if config_dir is None:
            config_dir = Path(os.getenv("UC_CONFIG_HOME", "."))
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"

    def load(self) -> HubitatConfig | None:
        """
        Load configuration from file.

        Returns:
            HubitatConfig if successful, None otherwise
        """
        if not self.config_file.exists():
            _LOG.warning("Configuration file does not exist")
            return None

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return HubitatConfig(
                hub_address=data.get("hub_address", ""),
                maker_api_id=data.get("maker_api_id", ""),
                access_token=data.get("access_token", ""),
            )
        except Exception as e:
            _LOG.error(f"Failed to load configuration: {e}")
            return None

    def save(self, config: HubitatConfig) -> bool:
        """
        Save configuration to file.

        Args:
            config: Configuration to save

        Returns:
            True if successful, False otherwise
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            data = {
                "hub_address": config.hub_address,
                "maker_api_id": config.maker_api_id,
                "access_token": config.access_token,
            }

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            _LOG.info("Configuration saved successfully")
            return True
        except Exception as e:
            _LOG.error(f"Failed to save configuration: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear configuration file.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.config_file.exists():
                self.config_file.unlink()
                _LOG.info("Configuration cleared")
            return True
        except Exception as e:
            _LOG.error(f"Failed to clear configuration: {e}")
            return False
