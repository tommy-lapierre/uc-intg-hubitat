"""Entity mapping between Hubitat devices and UC entities."""

import logging
from typing import Any
from enum import StrEnum

import ucapi

_LOG = logging.getLogger(__name__)


class HubitatCapability(StrEnum):
    """Hubitat device capabilities."""

    SWITCH = "Switch"
    SWITCH_LEVEL = "SwitchLevel"
    COLOR_CONTROL = "ColorControl"
    COLOR_TEMPERATURE = "ColorTemperature"
    LIGHT = "Light"
    LOCK = "Lock"
    THERMOSTAT = "Thermostat"
    TEMPERATURE_MEASUREMENT = "TemperatureMeasurement"
    CONTACT_SENSOR = "ContactSensor"
    MOTION_SENSOR = "MotionSensor"
    HUMIDITY_MEASUREMENT = "RelativeHumidityMeasurement"


class EntityMapper:
    """Maps Hubitat devices to Unfolded Circle entities."""

    @staticmethod
    def _normalize_attributes(attributes: Any) -> dict[str, Any]:
        """
        Convert Hubitat attributes format to simple dict.

        Hubitat returns attributes as list of objects:
        [{"name": "switch", "currentValue": "on", ...}, ...]

        We convert to: {"switch": "on", ...}
        """
        if isinstance(attributes, dict):
            return attributes

        if isinstance(attributes, list):
            normalized = {}
            for attr in attributes:
                if isinstance(attr, dict) and "name" in attr and "currentValue" in attr:
                    normalized[attr["name"]] = attr["currentValue"]
            return normalized

        return {}

    @staticmethod
    def get_entity_type(device: dict[str, Any]) -> str | None:
        """
        Determine UC entity type from Hubitat device capabilities.

        Args:
            device: Hubitat device information

        Returns:
            UC entity type or None if not supported
        """
        capabilities = device.get("capabilities", [])

        if isinstance(capabilities, list):
            cap_list = [cap if isinstance(cap, str) else cap.get("name", "") for cap in capabilities]
        else:
            cap_list = []

        # Check for climate/thermostat (check before lock since thermostats often have both)
        if HubitatCapability.THERMOSTAT in cap_list:
            return "climate"

        # Check for light capabilities
        if (
            HubitatCapability.LIGHT in cap_list
            or HubitatCapability.COLOR_CONTROL in cap_list
            or (HubitatCapability.SWITCH in cap_list and HubitatCapability.SWITCH_LEVEL in cap_list)
        ):
            return "light"

        # Check for switch
        if HubitatCapability.SWITCH in cap_list:
            return "switch"

        # Check for lock
        if HubitatCapability.LOCK in cap_list:
            return "lock"

        # Sensors aren't typically controllable entities
        _LOG.debug(f"Device {device.get('name')} has no supported entity type")
        return None

    @staticmethod
    def create_light_entity(device: dict[str, Any], cmd_handler) -> ucapi.Light:
        """
        Create UC light entity from Hubitat device.

        Args:
            device: Hubitat device information
            cmd_handler: Command handler function

        Returns:
            UC Light entity
        """
        device_id = str(device["id"])
        name = device.get("label") or device.get("name", f"Device {device_id}")

        capabilities = device.get("capabilities", [])
        cap_list = [cap if isinstance(cap, str) else cap.get("name", "") for cap in capabilities]

        features = [ucapi.light.Features.ON_OFF]

        # Check for dimming
        if HubitatCapability.SWITCH_LEVEL in cap_list:
            features.append(ucapi.light.Features.DIM)

        # Check for color
        if HubitatCapability.COLOR_CONTROL in cap_list:
            features.append(ucapi.light.Features.COLOR)

        # Check for color temperature
        if HubitatCapability.COLOR_TEMPERATURE in cap_list:
            features.append(ucapi.light.Features.COLOR_TEMPERATURE)

        # Get current state
        attributes = EntityMapper._normalize_attributes(device.get("attributes", {}))
        state = ucapi.light.States.OFF

        switch_state = attributes.get("switch", "off")
        if switch_state == "on":
            state = ucapi.light.States.ON

        # Create entity
        entity = ucapi.Light(
            identifier=device_id,
            name=name,
            features=features,
            attributes={"state": state},
            cmd_handler=cmd_handler,
        )

        # Set brightness if available
        if ucapi.light.Features.DIM in features:
            level = attributes.get("level", 0)
            if level is not None:
                entity.attributes["brightness"] = int(level)
            else:
                entity.attributes["brightness"] = 0

        # Set color if available
        if ucapi.light.Features.COLOR in features:
            hue = attributes.get("hue", 0)
            saturation = attributes.get("saturation", 0)
            if hue is not None and saturation is not None:
                entity.attributes["hue"] = float(hue)
                entity.attributes["saturation"] = float(saturation)
            else:
                entity.attributes["hue"] = 0.0
                entity.attributes["saturation"] = 0.0

        # Set color temperature if available
        if ucapi.light.Features.COLOR_TEMPERATURE in features:
            color_temp = attributes.get("colorTemperature", 0)
            if color_temp is not None:
                entity.attributes["color_temperature"] = int(color_temp)
            else:
                entity.attributes["color_temperature"] = 0

        return entity

    @staticmethod
    def create_climate_entity(device: dict[str, Any], cmd_handler) -> ucapi.Climate:
        """
        Create UC climate entity from Hubitat thermostat device.

        Args:
            device: Hubitat device information
            cmd_handler: Command handler function

        Returns:
            UC Climate entity
        """
        device_id = str(device["id"])
        name = device.get("label") or device.get("name", f"Device {device_id}")

        attributes = EntityMapper._normalize_attributes(device.get("attributes", {}))

        # Determine features based on supported modes
        features = [ucapi.climate.Features.ON_OFF]
        supported_modes_str = attributes.get("supportedThermostatModes", "[]")

        # Parse supported modes (it's a JSON string)
        import json
        try:
            supported_modes = json.loads(supported_modes_str) if isinstance(supported_modes_str, str) else supported_modes_str
        except:
            supported_modes = []

        if "heat" in supported_modes:
            features.append(ucapi.climate.Features.HEAT)
        if "cool" in supported_modes:
            features.append(ucapi.climate.Features.COOL)

        # Get current state
        current_mode = attributes.get("thermostatMode", "off")
        if current_mode == "off":
            state = ucapi.climate.States.OFF
        elif current_mode == "heat":
            state = ucapi.climate.States.HEAT
        elif current_mode == "cool":
            state = ucapi.climate.States.COOL
        elif current_mode == "auto":
            state = ucapi.climate.States.AUTO
        else:
            state = ucapi.climate.States.OFF

        # Create entity
        entity = ucapi.Climate(
            identifier=device_id,
            name=name,
            features=features,
            attributes={
                "state": state,
            },
            cmd_handler=cmd_handler,
        )

        # Set temperature attributes
        current_temp = attributes.get("temperature", 20)
        if current_temp is not None:
            entity.attributes["current_temperature"] = float(current_temp)
        else:
            entity.attributes["current_temperature"] = 20.0

        target_temp = attributes.get("thermostatSetpoint", 20)
        if target_temp is not None:
            entity.attributes["target_temperature"] = float(target_temp)
        else:
            entity.attributes["target_temperature"] = 20.0

        # Set heating/cooling setpoints if available
        if ucapi.climate.Features.HEAT in features:
            heat_setpoint = attributes.get("heatingSetpoint", 20)
            if heat_setpoint is not None:
                entity.attributes["target_temperature_heat"] = float(heat_setpoint)

        if ucapi.climate.Features.COOL in features:
            cool_setpoint = attributes.get("coolingSetpoint", 24)
            if cool_setpoint is not None:
                entity.attributes["target_temperature_cool"] = float(cool_setpoint)

        return entity

    @staticmethod
    def create_switch_entity(device: dict[str, Any], cmd_handler) -> ucapi.Switch:
        """
        Create UC switch entity from Hubitat device.

        Args:
            device: Hubitat device information
            cmd_handler: Command handler function

        Returns:
            UC Switch entity
        """
        device_id = str(device["id"])
        name = device.get("label") or device.get("name", f"Device {device_id}")

        attributes = EntityMapper._normalize_attributes(device.get("attributes", {}))
        state = ucapi.switch.States.OFF

        switch_state = attributes.get("switch", "off")
        if switch_state == "on":
            state = ucapi.switch.States.ON

        return ucapi.Switch(
            identifier=device_id,
            name=name,
            features=[ucapi.switch.Features.ON_OFF],
            attributes={"state": state},
            cmd_handler=cmd_handler,
        )

    @staticmethod
    def update_entity_state(entity: ucapi.Entity, device: dict[str, Any]) -> None:
        """
        Update entity state from Hubitat device attributes.

        Args:
            entity: UC entity to update
            device: Hubitat device information
        """
        attributes = EntityMapper._normalize_attributes(device.get("attributes", {}))

        # Update based on entity type
        if isinstance(entity, ucapi.Light):
            switch_state = attributes.get("switch", "off")
            entity.attributes["state"] = (
                ucapi.light.States.ON if switch_state == "on" else ucapi.light.States.OFF
            )

            if "level" in attributes:
                entity.attributes["brightness"] = int(attributes["level"])

            if "hue" in attributes:
                entity.attributes["hue"] = float(attributes["hue"])

            if "saturation" in attributes:
                entity.attributes["saturation"] = float(attributes["saturation"])

            if "colorTemperature" in attributes:
                entity.attributes["color_temperature"] = int(attributes["colorTemperature"])

        elif isinstance(entity, ucapi.Switch):
            switch_state = attributes.get("switch", "off")
            entity.attributes["state"] = (
                ucapi.switch.States.ON if switch_state == "on" else ucapi.switch.States.OFF
            )
