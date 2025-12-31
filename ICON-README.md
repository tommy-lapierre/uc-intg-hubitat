# Custom Icon Setup

## Current Status
The integration currently uses the built-in UC icon: `uc:integration`

## Adding a Custom Hubitat Icon

If you want to add a custom Hubitat logo icon:

### Requirements
- **Size:** 90×90 pixels
- **Format:** PNG or JPG
- **Max file size:** 32 KB
- **Filename:** hubitat.png (or any name you choose)

### Steps

1. **Create or download icon:**
   - Find/create a 90x90px Hubitat logo image
   - Optimize to be under 32 KB

2. **Add to repository:**
   ```bash
   # Place icon in root directory
   cp /path/to/your/hubitat.png ./hubitat.png
   ```

3. **Update driver.json:**
   ```json
   "icon": "custom:hubitat.png"
   ```

4. **Update build-integration.sh:**
   Uncomment this line (around line 51):
   ```bash
   cp hubitat.png artifacts/
   ```

5. **Rebuild package:**
   ```bash
   bash build-integration.sh
   ```

## Available Built-in Icons

Instead of a custom icon, you can use any of these built-in UC icons:
- `uc:integration` (current - generic integration icon)
- `uc:home` (house icon)
- `uc:light` (lightbulb icon)
- `uc:device` (generic device icon)

Just update the `icon` field in `intg-hubitat/driver.json`.
