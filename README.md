# 🌌 Space Weather Slackbot

> _Real-time space weather monitoring and alerting for Slack_

## Overview

This bot monitors space weather conditions from NOAA's Space Weather Prediction Center and sends automated Slack notifications for significant events. It tracks geomagnetic storms, solar flares, radiation storms, and solar wind conditions that can impact satellite operations, power grids, and communication systems.

### Key Features

- **Geomagnetic Storm Monitoring**: Alerts for Kp index ≥ 5 with graduated severity levels
- **Solar Flare Detection**: M-class and X-class flare notifications with flux measurements
- **Radiation Storm Alerts**: Proton flux monitoring with configurable thresholds
- **Solar Wind Speed Tracking**: Notifications for high-speed solar wind events
- **Daily Summaries**: Automated space weather briefings at configurable times
- **Duplicate Prevention**: Intelligent alert management to prevent notification spam

## Why Monitor Space Weather?

Space weather events can have significant impacts on:

- **Critical Infrastructure**: Power grid instabilities and potential blackouts
- **Satellite Operations**: Orbital decay, electronics damage, and communication disruption
- **Navigation Systems**: GPS/GNSS accuracy degradation and outages
- **Aviation**: Increased radiation exposure and HF radio blackouts
- **Communications**: Radio propagation anomalies and signal degradation

## Installation

### Prerequisites

- Docker (recommended) or Python 3.11+
- Slack incoming webhook URL
- Network access to NOAA SWPC APIs

### Docker Deployment

```bash
# Build the container
docker build -t space-weather-slackbot .

# Run with automatic restart
docker run -d \
  --name space-weather-slackbot \
  -e SLACK_WEBHOOK_URL="your_webhook_url" \
  --restart unless-stopped \
  space-weather-slackbot
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/kazazes/space-weather-slackbot.git
cd space-weather-slackbot

# Install dependencies
pip install -r requirements.txt

# Configure environment
export SLACK_WEBHOOK_URL="your_webhook_url"

# Run the bot
python main.py
```

## Creating a Slack Webhook

### Method 1: Using Slack App (Recommended)

1. **Go to Slack API Portal**
   - Visit https://api.slack.com/apps
   - Click "Create New App"
   - Choose "From scratch"
   - Name your app (e.g., "Space Weather Bot")
   - Select your workspace

2. **Enable Incoming Webhooks**
   - In your app settings, click "Incoming Webhooks" in the left sidebar
   - Toggle "Activate Incoming Webhooks" to ON
   - Scroll down and click "Add New Webhook to Workspace"

3. **Choose a Channel**
   - Select the channel where you want alerts to appear
   - Click "Allow"

4. **Copy Your Webhook URL**
   - You'll see a webhook URL like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`
   - Copy this URL - this is your `SLACK_WEBHOOK_URL`

### Method 2: Using Slack Workspace Settings (If Available)

1. **Open Slack Workspace Settings**
   - In Slack, click your workspace name
   - Select "Settings & administration" → "Manage apps"

2. **Search for Webhooks**
   - Search for "Incoming WebHooks"
   - Click "Add to Slack"

3. **Configure the Webhook**
   - Choose a channel
   - Click "Add Incoming WebHooks integration"
   - Copy the webhook URL

### Testing Your Webhook

You can test if your webhook is working with a simple curl command:

```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Hello from Space Weather Bot! 🚀"}' \
  YOUR_WEBHOOK_URL
```

### Important Notes

- **Keep your webhook URL secret** - anyone with the URL can post to your channel
- The bot will use `<!channel>` mentions for alerts, so it will notify everyone in the channel
- You can create multiple webhooks for different channels if needed
- If you need to revoke access, you can regenerate or delete the webhook in your Slack app settings

## Configuration

### Alert Thresholds

The bot uses the following scientifically-established thresholds:

| Alert Type              | Threshold     | Impact Level                             |
| ----------------------- | ------------- | ---------------------------------------- |
| Minor Geomagnetic Storm | Kp ≥ 5        | G1 - Minor impacts on satellites         |
| Moderate Storm          | Kp ≥ 6        | G2 - Voltage alarms in power systems     |
| Strong Storm            | Kp ≥ 7        | G3 - Satellite orientation corrections   |
| Severe Storm            | Kp ≥ 8        | G4 - Widespread voltage control issues   |
| Extreme Storm           | Kp = 9        | G5 - Grid system collapse possible       |
| M-class Flare           | ≥ 1×10⁻⁵ W/m² | R1-R2 - Minor to moderate radio blackout |
| X-class Flare           | ≥ 1×10⁻⁴ W/m² | R3-R5 - Strong to extreme radio blackout |
| Radiation Storm         | ≥ 10 pfu      | S1+ - Elevated radiation levels          |
| High Solar Wind         | ≥ 600 km/s    | Enhanced geomagnetic activity expected   |

### Environment Variables

- `SLACK_WEBHOOK_URL`: Slack incoming webhook URL (required)
- `DAILY_SUMMARY_HOUR`: Hour for daily summary delivery (default: 9, range: 0-23)

### Customization

Thresholds can be modified in `main.py` based on your specific monitoring requirements:

```python
GEOSTORM_THRESHOLDS = {
    "Minor": 5,
    "Moderate": 6,
    "Strong": 7,
    "Severe": 8,
    "Extreme": 9
}

FLARE_THRESHOLDS = {
    "M": 1e-5,  # M-class threshold
    "X": 1e-4   # X-class threshold
}

PROTON_FLUX_THRESHOLD = 10  # pfu
SOLAR_WIND_SPEED_THRESHOLD = 600  # km/s
```

## Technical Details

### Data Sources

The bot consumes real-time data from NOAA SWPC JSON APIs:

- Planetary K-index (1-minute resolution)
- GOES X-ray flux (1-day dataset)
- GOES proton flux (integral measurements)
- DSCOVR solar wind parameters

### Architecture

- **Polling Interval**: 5 minutes
- **Alert Deduplication**: State-based tracking prevents duplicate notifications
- **Error Handling**: Graceful degradation with automatic retry
- **Resource Usage**: Minimal CPU and memory footprint

### Alert Format

Notifications include:

- Alert type and severity
- Measured values with timestamps
- Direct links to SWPC data and solar imagery

Example:

```
🚨 Geomagnetic Storm Alert
Strong Storm (Kp 7.3) at 2024-01-15T14:30:00Z
SWPC Data | Solar Imagery
```

## Monitoring and Maintenance

### Health Checks

The bot includes error handling for:

- Network connectivity issues
- API endpoint failures
- Invalid data formats
- Slack webhook failures

### Logging

All errors are printed to stdout with timestamps. For production deployments, consider redirecting logs to a persistent storage solution.

### Performance

- Average memory usage: < 50MB
- CPU usage: < 1% (spike during API calls)
- Network bandwidth: ~100KB/hour

## Contributing

Contributions are welcome. Please ensure:

- Code follows PEP 8 style guidelines
- All API calls include proper error handling
- New features include appropriate documentation
- Threshold changes are scientifically justified

## License

MIT License

## Acknowledgments

- NOAA Space Weather Prediction Center for providing public access to space weather data
- The space weather research community for establishing monitoring standards

---

_For questions about space weather impacts or monitoring requirements, consult the [NOAA Space Weather Scales](https://www.swpc.noaa.gov/noaa-scales-explanation)_
