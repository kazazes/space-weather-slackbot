# 🌌 Space Weather Slackbot

> *Quick hack for real-time space weather alerts in Slack*

Keep tabs on space weather (geomagnetic storms, solar flares, radiation bursts, and  solar wind conditions).

* **Geomagnetic Storm Alerts**: Pings when Kp index goes 5+ (real-deal solar turbulence)
* **Solar Flare Notifications**: Shouts out when there's an M-class or X-class flare
* **Radiation Storm Warnings**: Proton flux spikes get immediate notice
* **Solar Wind Updates**: Flags high-speed events bc satellites don’t love surprises
* **Daily Briefing**: Morning updates because a morning without space weather is lame

## Slack Webhook Setup

1. Go to [Slack API](https://api.slack.com/apps).
2. New App → Activate Webhooks → Add webhook to your workspace.
3. Copy your URL like `https://hooks.slack.com/...`

Test:

```bash
curl -X POST -H 'Content-type: application/json' \
--data '{"text":"Space weather bot says hi 🚀"}' YOUR_WEBHOOK_URL
```

## Alerts & Thresholds

Defaults are reasonable (scientifically informed vibes):

| Alert            | Threshold    |
| ---------------- | ------------ |
| Minor Storm      | Kp 5         |
| Moderate Storm   | Kp 6         |
| Strong Storm     | Kp 7         |
| Severe Storm     | Kp 8         |
| Extreme Storm    | Kp 9         |
| M-class Flare    | ≥1×10⁻⁵ W/m² |
| X-class Flare    | ≥1×10⁻⁴ W/m² |
| Radiation Storm  | ≥10 pfu      |
| Solar Wind Speed | ≥600 km/s    |

Data fetched every 5 min from NOAA SWPC APIs

Example notification:

```
🚨 Geomagnetic Storm
Strong Storm (Kp 7.3)
SWPC Data | Solar Imagery
```

## License

MIT

Thank you SWPC.
