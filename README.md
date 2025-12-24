# Hubitat Integration for Unfolded Circle Remote

This integration allows you to control your Hubitat Elevation smart home devices using an Unfolded Circle Remote Two.

## Features

- Control Hubitat devices through Unfolded Circle Remote
- Support for multiple device types:
  - Lights (on/off, dimming, color, color temperature)
  - Switches (on/off)
- Real-time device state synchronization
- Easy setup through Remote's configuration interface

## Prerequisites

- Hubitat Elevation hub (firmware 2.3.0 or newer recommended)
- Unfolded Circle Remote Two
- Python 3.11 or newer
- Maker API enabled on your Hubitat hub

## Hubitat Setup

1. Log in to your Hubitat web interface
2. Navigate to **Apps** → **Add Built-In App**
3. Select **Maker API**
4. Select the devices you want to control with the Remote
5. Note down:
   - Your hub's IP address
   - The Maker API App ID (shown in the app URL)
   - The Access Token (shown in the Maker API app)

## Installation

### Option 1: Run from Source

1. Clone this repository:
```bash
git clone https://github.com/tommy-lapierre/uc-intg-hubitat.git
cd uc-intg-hubitat
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the integration:
```bash
python intg-hubitat/driver.py
```

### Option 2: Install as Package (Future)

This integration will be available through the Unfolded Circle integration store.

## Configuration

### First-Time Setup

1. On your Unfolded Circle Remote, navigate to **Settings** → **Integrations**
2. Select **Add Integration** → **Hubitat Elevation**
3. Enter your Hubitat hub details:
   - **Hub IP Address**: Your Hubitat hub's local IP (e.g., 192.168.1.100)
   - **Maker API App ID**: The app ID from your Maker API (e.g., 123)
   - **Access Token**: Your Maker API access token

4. The integration will connect to your hub and discover all enabled devices
5. Select which devices you want to add to your Remote

### Environment Variables

You can customize the integration behavior using environment variables:

- `UC_CONFIG_HOME`: Configuration directory (default: current directory)
- `UC_INTEGRATION_INTERFACE`: WebSocket listening address (default: 0.0.0.0)
- `UC_INTEGRATION_HTTP_PORT`: Custom port (default: 9087)
- `UC_DISABLE_MDNS_PUBLISH`: Disable mDNS service discovery (default: false)

## Supported Device Types

### Lights
- **On/Off Control**: Basic power control
- **Dimming**: Brightness adjustment (0-100%)
- **Color Control**: RGB color selection via hue/saturation
- **Color Temperature**: Adjustable white color temperature

Hubitat Capabilities Mapped:
- `Switch` + `SwitchLevel` → Dimmable Light
- `ColorControl` → RGB Color Support
- `ColorTemperature` → Color Temperature Support

### Switches
- **On/Off Control**: Basic power control

Hubitat Capabilities Mapped:
- `Switch` → Switch Entity

## Troubleshooting

### Integration Won't Connect

1. Verify your Hubitat hub is reachable from the Remote
2. Check that the Maker API is enabled and configured correctly
3. Verify the App ID and Access Token are correct
4. Ensure devices are selected in the Maker API app

### Devices Not Showing Up

1. Check that devices are enabled in the Maker API app
2. Verify the devices have supported capabilities (Switch, Light, etc.)
3. Check the integration logs for errors

### Commands Not Working

1. Verify the device supports the command in Hubitat
2. Check Hubitat logs for errors
3. Try controlling the device directly from Hubitat to confirm it's working

## Development

### Project Structure

```
uc-intg-hubitat/
├── intg-hubitat/
│   ├── driver.json       # Integration metadata
│   ├── driver.py         # Main driver code
│   ├── config.py         # Configuration management
│   ├── hubitat.py        # Hubitat API client
│   └── entities.py       # Entity mapping logic
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── CLAUDE.MD            # AI assistant context
```

### Running in Development Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run the integration
python intg-hubitat/driver.py
```

### Adding Support for New Device Types

1. Add capability mapping in `entities.py` → `HubitatCapability`
2. Update `EntityMapper.get_entity_type()` to detect the new device type
3. Create entity factory method (e.g., `create_climate_entity()`)
4. Add command handler logic in `driver.py` → `device_command_handler()`

## Known Limitations

- Sensors (temperature, motion, contact) are read-only and not exposed as controllable entities
- Climate/thermostat support is planned but not yet implemented
- Lock support is planned but not yet implemented
- No support for scenes or modes yet
- Device state polling is not implemented (relies on initial state only)

## Future Enhancements

- [ ] Device state polling/updates
- [ ] WebSocket event stream from Hubitat
- [ ] Climate/thermostat control
- [ ] Lock control
- [ ] Scene activation
- [ ] Mode selection
- [ ] Sensor data display
- [ ] Custom device grouping

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0).

## Support

- **Issues**: [GitHub Issues](https://github.com/tommy-lapierre/uc-intg-hubitat/issues)
- **Hubitat Documentation**: https://docs2.hubitat.com/
- **Unfolded Circle Developers**: https://www.unfoldedcircle.com/developers

## Acknowledgments

- Built using the [Unfolded Circle Python Integration Library](https://github.com/unfoldedcircle/integration-python-library)
- Inspired by other UC integrations in the community
- Thanks to the Hubitat and Unfolded Circle communities

---

**Note**: This integration is not officially affiliated with Hubitat or Unfolded Circle. It is a community-developed project.
