# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Hubitat Integration for Unfolded Circle Remote Two**

This is a Python-based integration driver that connects Hubitat Elevation smart home hubs with Unfolded Circle Remote Two devices. The integration uses the Hubitat Maker API and the Unfolded Circle Python Integration Library (ucapi) to enable control of Hubitat devices through the Remote interface.

**Repository:** https://github.com/tommy-lapierre/uc-intg-hubitat.git
**License:** Mozilla Public License 2.0 (MPL-2.0)

## Technology Stack

- **Language:** Python 3.11+
- **Key Dependencies:**
  - `ucapi>=0.5.0` (currently 0.5.1) - Unfolded Circle Integration API
  - `aiohttp>=3.9.0` - Async HTTP client for Hubitat API
  - `asyncio-mqtt>=0.16.0` - MQTT support (future use)
- **Protocols:** HTTP/REST (Hubitat Maker API), WebSocket (UC Remote communication)

## Common Commands

### Development Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Integration

```bash
# Run with standard logging
python intg-hubitat/driver.py

# Run with debug logging
LOG_LEVEL=DEBUG python intg-hubitat/driver.py
```

### Environment Variables

- `UC_CONFIG_HOME` - Configuration directory (default: current directory)
- `UC_INTEGRATION_INTERFACE` - WebSocket listening address (default: 0.0.0.0)
- `UC_INTEGRATION_HTTP_PORT` - Custom port (default: 9087)
- `UC_DISABLE_MDNS_PUBLISH` - Disable mDNS service discovery
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Architecture

### Core Components

**driver.py** - Main integration driver
- Entry point and event loop management
- Handles UC Remote lifecycle events (CONNECT, DISCONNECT, STANDBY)
- Setup flow coordination (driver_setup_handler, handle_user_data_response)
- Device command dispatch to Hubitat hub
- Entity subscription management

**hubitat.py** - Hubitat Maker API client
- HTTP client wrapper for Hubitat Maker API endpoints
- Methods: get_all_devices(), get_device(), send_command(), test_connection()
- Manages aiohttp session lifecycle

**entities.py** - Entity mapping and conversion
- Maps Hubitat capabilities to UC entity types (Light, Switch, etc.)
- HubitatCapability enum defines supported capabilities
- EntityMapper handles device-to-entity conversion logic
- Creates UC entities with appropriate features based on device capabilities

**config.py** - Configuration persistence
- Manages HubitatConfig (hub_address, maker_api_id, access_token)
- JSON-based storage in UC_CONFIG_HOME/config.json
- Handles config load/save/clear operations

**driver.json** - Integration metadata
- Defines driver ID, version, compatibility, and setup schema
- Multilingual name/description support
- Configuration UI definition for Remote setup flow

### Data Flow

1. **Setup Flow:** Remote requests setup → driver.py requests user input → user provides Hubitat credentials → test connection → save config → discover devices → create entities
2. **Command Flow:** Remote sends command → driver.py receives via ucapi → hubitat.py sends HTTP request to Maker API → device state updated locally
3. **Entity Management:** Entities discovered at startup → added to available_entities → Remote subscribes → added to configured_entities

### Entity Type Detection Logic

Hubitat devices are mapped based on capabilities:
- **Light:** Has Light capability OR ColorControl OR (Switch + SwitchLevel)
- **Switch:** Has Switch capability only
- **Lock/Climate:** Defined but not implemented yet
- **Sensors:** Detected but not exposed as controllable entities

### State Management

- Initial device state fetched from Hubitat on discovery
- Commands update local entity attributes immediately
- No polling or real-time updates from Hubitat (known limitation)
- State synchronization relies on command success assumptions

## Key Implementation Details

### Command Handler Pattern

All entities use `device_command_handler()` which:
1. Validates hubitat_client is initialized
2. Dispatches based on entity type (Light vs Switch)
3. Maps UC commands to Hubitat commands
4. Updates local entity attributes
5. Calls `api.configured_entities.update_attributes()` to sync with Remote

**Important:** In ucapi 0.5.x, lights only have three commands (ON, OFF, TOGGLE). Advanced features like dimming, color, and color temperature are handled via parameters passed with the ON command:
- `ON` with `brightness` param → calls Hubitat `setLevel`
- `ON` with `hue`/`saturation` params → calls Hubitat `setColor`
- `ON` with `color_temperature` param → calls Hubitat `setColorTemperature`

### Hubitat Maker API URL Format

```
http://{hub_address}/apps/api/{app_id}/devices?access_token={token}
http://{hub_address}/apps/api/{app_id}/devices/{device_id}?access_token={token}
http://{hub_address}/apps/api/{app_id}/devices/{device_id}/{command}?access_token={token}
http://{hub_address}/apps/api/{app_id}/devices/{device_id}/{command}/{param1}/{param2}?access_token={token}
```

### Adding New Device Types

To add support for new device types (e.g., climate, locks):

1. Add capability constant in `entities.py` → `HubitatCapability`
2. Update `EntityMapper.get_entity_type()` detection logic
3. Create factory method (e.g., `create_climate_entity()`)
4. Add command handler branch in `driver.py` → `device_command_handler()`
5. Test with actual Hubitat device

### Async/Await Conventions

- All device operations are async (Hubitat API, UC events)
- Use `await` for all I/O operations
- Main event loop runs in `loop.run_forever()`
- Clean shutdown closes hubitat_client session

## Known Limitations

- **No real-time state updates:** Device states not polled or pushed from Hubitat
- **No WebSocket event stream:** Planned but not implemented
- **Limited device types:** Only lights and switches currently supported
- **No scene/mode support:** Not yet implemented
- **Color command format:** Uses hue/saturation dict, may need adjustment for specific devices

## Hubitat Maker API Reference

Key endpoints used:
- `GET /apps/api/{app_id}/devices` - List all devices
- `GET /apps/api/{app_id}/devices/{device_id}` - Get device details
- `GET /apps/api/{app_id}/devices/{device_id}/{command}` - Send command

Commands used:
- `on`, `off` - Switch/light control
- `setLevel` - Dimming (parameter: 0-100)
- `setColor` - Color control (parameter: {hue: 0-100, saturation: 0-100})
- `setColorTemperature` - Color temperature (parameter: Kelvin value)

## Unfolded Circle Integration Patterns

- Integration uses UC Python Integration Library (ucapi)
- Driver runs as standalone process communicating via WebSocket
- Setup flow uses RequestUserInput/SetupComplete/SetupError pattern
- Entity lifecycle: available_entities (discovered) → configured_entities (subscribed)
- Command handlers must return StatusCodes (OK, SERVICE_UNAVAILABLE, SERVER_ERROR)

## Troubleshooting Tips

- Check Hubitat hub is reachable on local network
- Verify Maker API app is installed and devices are selected
- Confirm App ID and Access Token are correct
- Review logs for HTTP errors from Hubitat API
- Test connection using test_connection() method
- Ensure Python 3.11+ is being used

## Resources

- **Hubitat Documentation:** https://docs2.hubitat.com/
- **Unfolded Circle Developer Docs:** https://www.unfoldedcircle.com/developers
- **UC Integration Python Library:** https://github.com/unfoldedcircle/integration-python-library
