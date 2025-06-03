# Gira X1 Home Assistant Integration

A custom Home Assistant integration for Gira X1 home automation systems using the REST API.

## Features

- **Lights**: Control switches and dimmers with brightness and shift support
- **Covers**: Control blinds and shutters with position and tilt support  
- **Climate**: Temperature control for heating/cooling systems
- **Buttons**: Trigger functions and scene activation
- **Sensors**: Temperature, humidity, and custom sensors
- **Binary Sensors**: Motion, presence, door, and window detection
- **Switches**: Generic on/off switches
- **Dual Authentication**: Username/password or API token authentication

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL: `https://github.com/heikoburkhardt/gira-x1-ha`
5. Select "Integration" as the category
6. Click "Add"
7. Find "Gira X1" in the HACS integration list and install it
8. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/gira_x1` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

### Via UI (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Gira X1"
4. Enter your Gira X1 device details:
   - **Host**: IP address of your Gira X1 device
   - **Port**: REST API port (default: 80)
   - **Authentication Method**: Choose between username/password or token
   
#### Username/Password Authentication
   - **Username**: Your Gira X1 username
   - **Password**: Your Gira X1 password

#### Token Authentication
   - **API Token**: Your pre-generated Gira X1 API token

### Via YAML (Optional)

#### Username/Password Method
```yaml
gira_x1:
  host: "192.168.1.100"
  port: 80
  auth_method: "password"
  username: "your_username"
  password: "your_password"
```

#### Token Method
```yaml
gira_x1:
  host: "192.168.1.100"
  port: 80
  auth_method: "token"
  token: "your_api_token"
```

### Getting an API Token

See [TOKEN_AUTHENTICATION.md](TOKEN_AUTHENTICATION.md) for detailed instructions on obtaining and using API tokens.

## API Requirements

This integration requires:
- Gira X1 device with REST API v2 enabled
- Valid API credentials
- Network connectivity between Home Assistant and the Gira X1 device

## Supported Device Types

| Gira Function Type | Home Assistant Platform | Description |
|-------------------|------------------------|-------------|
| de.gira.schema.functions.Switch | Switch | Binary on/off control |
| de.gira.schema.functions.KNX.Light | Light | Brightness and color control |
| de.gira.schema.functions.Covering | Cover | Position and tilt control |
| de.gira.schema.functions.KNX.HeatingCooling | Climate | Temperature control |
| de.gira.schema.functions.Trigger | Button | Scene and trigger activation |
| Temperature Sensors | Sensor | Temperature readings |
| Humidity Sensors | Sensor | Humidity readings |
| Motion/Presence | Binary Sensor | Occupancy detection |

*Complete mapping validated against real Gira X1 device with 180 functions*

## Troubleshooting

### Common Issues

1. **Cannot Connect**: Verify the IP address and port are correct
2. **Invalid Authentication**: Check username and password
3. **No Devices Found**: Ensure the Gira X1 has configured functions

### Debug Logging

Add the following to your `configuration.yaml` to enable debug logging:

```yaml
logger:
  default: warning
  logs:
    custom_components.gira_x1: debug
```

## API Documentation

This integration is based on the Gira IoT REST API v2. Refer to the official Gira documentation for detailed API specifications.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This is an unofficial integration not affiliated with Gira. Use at your own risk.
