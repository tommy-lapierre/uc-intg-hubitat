#!/usr/bin/env python3
"""Hubitat integration driver for Unfolded Circle Remote."""

import asyncio
import logging
from typing import Any

import ucapi
from ucapi import IntegrationAPI, StatusCodes

from config import ConfigurationManager, HubitatConfig
from entities import EntityMapper
from hubitat import HubitatClient

_LOG = logging.getLogger(__name__)

# Global instances
loop = asyncio.new_event_loop()
api = IntegrationAPI(loop)
config_manager = ConfigurationManager()
hubitat_client: HubitatClient | None = None
entities: dict[str, ucapi.Entity] = {}


async def device_command_handler(
    entity: ucapi.Entity, cmd_id: str, params: dict[str, Any] | None, websocket: Any
) -> StatusCodes:
    """
    Handle commands for devices.

    Args:
        entity: Entity receiving the command
        cmd_id: Command identifier
        params: Command parameters
        websocket: WebSocket connection

    Returns:
        Status code
    """
    if hubitat_client is None:
        _LOG.error("Hubitat client not initialized")
        return StatusCodes.SERVICE_UNAVAILABLE

    device_id = entity.id
    _LOG.info(f"Received command {cmd_id} for device {device_id}")

    try:
        # Handle light commands
        if isinstance(entity, ucapi.Light):
            if cmd_id == ucapi.light.Commands.ON:
                # Handle ON command with optional parameters for brightness, color, etc.
                if params:
                    # Handle brightness
                    if "brightness" in params:
                        brightness = params["brightness"]
                        await hubitat_client.send_command(device_id, "setLevel", [brightness])
                        entity.attributes["brightness"] = brightness

                    # Handle color (hue/saturation)
                    if "hue" in params and "saturation" in params:
                        hue = params["hue"]
                        saturation = params["saturation"]
                        await hubitat_client.send_command(device_id, "setColor", [{"hue": hue, "saturation": saturation}])
                        entity.attributes["hue"] = hue
                        entity.attributes["saturation"] = saturation

                    # Handle color temperature
                    if "color_temperature" in params:
                        color_temp = params["color_temperature"]
                        await hubitat_client.send_command(device_id, "setColorTemperature", [color_temp])
                        entity.attributes["color_temperature"] = color_temp

                # Always turn on
                await hubitat_client.send_command(device_id, "on")
                entity.attributes["state"] = ucapi.light.States.ON

            elif cmd_id == ucapi.light.Commands.OFF:
                await hubitat_client.send_command(device_id, "off")
                entity.attributes["state"] = ucapi.light.States.OFF

            elif cmd_id == ucapi.light.Commands.TOGGLE:
                current_state = entity.attributes.get("state", ucapi.light.States.OFF)
                if current_state == ucapi.light.States.ON:
                    await hubitat_client.send_command(device_id, "off")
                    entity.attributes["state"] = ucapi.light.States.OFF
                else:
                    await hubitat_client.send_command(device_id, "on")
                    entity.attributes["state"] = ucapi.light.States.ON

            api.configured_entities.update_attributes(entity.id, entity.attributes)

        # Handle switch commands
        elif isinstance(entity, ucapi.Switch):
            if cmd_id == ucapi.switch.Commands.ON:
                await hubitat_client.send_command(device_id, "on")
                entity.attributes["state"] = ucapi.switch.States.ON

            elif cmd_id == ucapi.switch.Commands.OFF:
                await hubitat_client.send_command(device_id, "off")
                entity.attributes["state"] = ucapi.switch.States.OFF

            elif cmd_id == ucapi.switch.Commands.TOGGLE:
                current_state = entity.attributes.get("state", ucapi.switch.States.OFF)
                if current_state == ucapi.switch.States.ON:
                    await hubitat_client.send_command(device_id, "off")
                    entity.attributes["state"] = ucapi.switch.States.OFF
                else:
                    await hubitat_client.send_command(device_id, "on")
                    entity.attributes["state"] = ucapi.switch.States.ON

            api.configured_entities.update_attributes(entity.id, entity.attributes)

        # Handle climate commands
        elif isinstance(entity, ucapi.Climate):
            if cmd_id == ucapi.climate.Commands.ON:
                # Turn on to last mode (default to heat)
                last_mode = entity.attributes.get("state", ucapi.climate.States.HEAT)
                if last_mode == ucapi.climate.States.OFF:
                    last_mode = ucapi.climate.States.HEAT

                if last_mode == ucapi.climate.States.HEAT:
                    await hubitat_client.send_command(device_id, "heat")
                    entity.attributes["state"] = ucapi.climate.States.HEAT
                elif last_mode == ucapi.climate.States.COOL:
                    await hubitat_client.send_command(device_id, "cool")
                    entity.attributes["state"] = ucapi.climate.States.COOL
                elif last_mode == ucapi.climate.States.AUTO:
                    await hubitat_client.send_command(device_id, "auto")
                    entity.attributes["state"] = ucapi.climate.States.AUTO

            elif cmd_id == ucapi.climate.Commands.OFF:
                await hubitat_client.send_command(device_id, "off")
                entity.attributes["state"] = ucapi.climate.States.OFF

            elif cmd_id == ucapi.climate.Commands.HVAC_MODE:
                # Change HVAC mode
                if params and "hvac_mode" in params:
                    mode = params["hvac_mode"]
                    if mode == "off":
                        await hubitat_client.send_command(device_id, "off")
                        entity.attributes["state"] = ucapi.climate.States.OFF
                    elif mode == "heat":
                        await hubitat_client.send_command(device_id, "heat")
                        entity.attributes["state"] = ucapi.climate.States.HEAT
                    elif mode == "cool":
                        await hubitat_client.send_command(device_id, "cool")
                        entity.attributes["state"] = ucapi.climate.States.COOL
                    elif mode == "auto":
                        await hubitat_client.send_command(device_id, "auto")
                        entity.attributes["state"] = ucapi.climate.States.AUTO

            elif cmd_id == ucapi.climate.Commands.TARGET_TEMPERATURE:
                # Set target temperature
                if params and "temperature" in params:
                    temp = params["temperature"]
                    current_state = entity.attributes.get("state", ucapi.climate.States.HEAT)

                    if current_state == ucapi.climate.States.HEAT:
                        await hubitat_client.send_command(device_id, "setHeatingSetpoint", [temp])
                        entity.attributes["target_temperature_heat"] = float(temp)
                        entity.attributes["target_temperature"] = float(temp)
                    elif current_state == ucapi.climate.States.COOL:
                        await hubitat_client.send_command(device_id, "setCoolingSetpoint", [temp])
                        entity.attributes["target_temperature_cool"] = float(temp)
                        entity.attributes["target_temperature"] = float(temp)
                    else:
                        # If in auto or off mode, set heating setpoint by default
                        await hubitat_client.send_command(device_id, "setHeatingSetpoint", [temp])
                        entity.attributes["target_temperature"] = float(temp)

            elif cmd_id == ucapi.climate.Commands.TARGET_TEMPERATURE_HEAT:
                # Set heating target temperature
                if params and "temperature" in params:
                    temp = params["temperature"]
                    await hubitat_client.send_command(device_id, "setHeatingSetpoint", [temp])
                    entity.attributes["target_temperature_heat"] = float(temp)
                    entity.attributes["target_temperature"] = float(temp)

            elif cmd_id == ucapi.climate.Commands.TARGET_TEMPERATURE_COOL:
                # Set cooling target temperature
                if params and "temperature" in params:
                    temp = params["temperature"]
                    await hubitat_client.send_command(device_id, "setCoolingSetpoint", [temp])
                    entity.attributes["target_temperature_cool"] = float(temp)
                    entity.attributes["target_temperature"] = float(temp)

            api.configured_entities.update_attributes(entity.id, entity.attributes)

        return StatusCodes.OK

    except Exception as e:
        _LOG.error(f"Error handling command: {e}")
        return StatusCodes.SERVER_ERROR


async def load_devices():
    """Load devices from Hubitat and create entities."""
    global entities

    if hubitat_client is None:
        _LOG.error("Hubitat client not initialized")
        return

    _LOG.info("Loading devices from Hubitat")

    try:
        devices = await hubitat_client.get_all_devices()

        for device in devices:
            entity_type = EntityMapper.get_entity_type(device)

            if entity_type is None:
                continue

            device_id = str(device["id"])

            # Create appropriate entity
            if entity_type == "light":
                entity = EntityMapper.create_light_entity(device, device_command_handler)
            elif entity_type == "switch":
                entity = EntityMapper.create_switch_entity(device, device_command_handler)
            elif entity_type == "climate":
                entity = EntityMapper.create_climate_entity(device, device_command_handler)
            else:
                continue

            entities[device_id] = entity
            api.available_entities.add(entity)
            _LOG.info(f"Added {entity_type} entity: {entity.name} (ID: {device_id})")

        _LOG.info(f"Loaded {len(entities)} entities")

    except Exception as e:
        _LOG.error(f"Error loading devices: {e}")


@api.listens_to(ucapi.Events.CONNECT)
async def on_connect() -> None:
    """Handle connection event."""
    _LOG.info("Remote connected")
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)


@api.listens_to(ucapi.Events.DISCONNECT)
async def on_disconnect() -> None:
    """Handle disconnection event."""
    _LOG.info("Remote disconnected")


@api.listens_to(ucapi.Events.ENTER_STANDBY)
async def on_enter_standby() -> None:
    """Handle standby event."""
    _LOG.info("Remote entered standby")


@api.listens_to(ucapi.Events.EXIT_STANDBY)
async def on_exit_standby() -> None:
    """Handle exit standby event."""
    _LOG.info("Remote exited standby")


@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """
    Handle entity subscription.

    Args:
        entity_ids: List of entity IDs being subscribed to
    """
    _LOG.info(f"Subscribed to entities: {entity_ids}")

    for entity_id in entity_ids:
        if entity_id in entities:
            api.configured_entities.add(entities[entity_id])


@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
async def on_unsubscribe_entities(entity_ids: list[str]) -> None:
    """
    Handle entity unsubscription.

    Args:
        entity_ids: List of entity IDs being unsubscribed from
    """
    _LOG.info(f"Unsubscribed from entities: {entity_ids}")

    for entity_id in entity_ids:
        api.configured_entities.remove(entity_id)


async def handle_driver_setup(msg: ucapi.SetupDriver) -> ucapi.SetupAction:
    """
    Handle driver setup process.

    Args:
        msg: Setup driver message

    Returns:
        Setup action (request user input or complete setup)
    """
    _LOG.info("Starting driver setup")

    if msg.reconfigure:
        _LOG.info("Reconfiguring driver")
        config_manager.clear()

    # If setup_data is provided, process it directly
    if msg.setup_data:
        _LOG.info("Setup data provided, processing directly")
        # Convert setup_data dict to UserDataResponse
        user_data = ucapi.UserDataResponse(
            input_values=msg.setup_data
        )
        return await handle_user_data_response(user_data)

    # Otherwise, request Hubitat configuration
    return ucapi.RequestUserInput(
        {"en": "Hubitat Configuration"},
        [
            {
                "field": {"text": {"value": ""}},
                "id": "hub_address",
                "label": {
                    "en": "Hub IP Address or Hostname",
                },
            },
            {
                "field": {"text": {"value": ""}},
                "id": "maker_api_id",
                "label": {
                    "en": "Maker API App ID",
                },
            },
            {
                "field": {"text": {"value": ""}},
                "id": "access_token",
                "label": {
                    "en": "Maker API Access Token",
                },
            },
        ],
    )


async def handle_user_data_response(msg: ucapi.UserDataResponse) -> ucapi.SetupAction:
    """
    Handle user input during setup.

    Args:
        msg: User data response

    Returns:
        Setup action (error or complete)
    """
    global hubitat_client

    _LOG.info("Processing user input")

    hub_address = msg.input_values.get("hub_address", "")
    maker_api_id = msg.input_values.get("maker_api_id", "")
    access_token = msg.input_values.get("access_token", "")

    if not hub_address or not maker_api_id or not access_token:
        _LOG.error("Missing required configuration")
        return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.OTHER)

    # Test connection
    test_client = HubitatClient(hub_address, maker_api_id, access_token)
    if not await test_client.test_connection():
        _LOG.error("Failed to connect to Hubitat hub")
        await test_client.close()
        return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.CONNECTION_REFUSED)

    await test_client.close()

    # Save configuration
    config = HubitatConfig(
        hub_address=hub_address,
        maker_api_id=maker_api_id,
        access_token=access_token,
    )

    if not config_manager.save(config):
        _LOG.error("Failed to save configuration")
        return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.OTHER)

    # Initialize client
    hubitat_client = HubitatClient(hub_address, maker_api_id, access_token)

    # Load devices
    await load_devices()

    _LOG.info("Setup completed successfully")
    return ucapi.SetupComplete()


async def driver_setup_handler(msg: ucapi.SetupDriver) -> ucapi.SetupAction:
    """
    Dispatch driver setup messages.

    Args:
        msg: Setup message

    Returns:
        Setup action
    """
    if isinstance(msg, ucapi.SetupDriver):
        return await handle_driver_setup(msg)
    elif isinstance(msg, ucapi.UserDataResponse):
        return await handle_user_data_response(msg)
    elif isinstance(msg, ucapi.AbortDriverSetup):
        _LOG.info("Setup aborted by user")
        return ucapi.SetupError()
    else:
        _LOG.error(f"Unsupported setup message: {msg}")
        return ucapi.SetupError()


async def main():
    """Initialize and run the integration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    _LOG.info("Starting Hubitat integration driver")

    global hubitat_client

    # Load existing configuration
    config = config_manager.load()
    if config:
        _LOG.info("Loading configuration")
        hubitat_client = HubitatClient(
            config.hub_address,
            config.maker_api_id,
            config.access_token,
        )
        await load_devices()
        await api.set_device_state(ucapi.DeviceStates.CONNECTED)
    else:
        _LOG.info("No configuration found, waiting for setup")

    # Initialize the API
    await api.init("intg-hubitat/driver.json", driver_setup_handler)


if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        _LOG.info("Shutting down")
    finally:
        if hubitat_client:
            loop.run_until_complete(hubitat_client.close())
        loop.close()
