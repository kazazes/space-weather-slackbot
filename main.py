import requests
import time
import os
import datetime
import sys
import logging

logging.basicConfig(level=logging.INFO)


# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

# NOAA and Space Weather URLs
K_INDEX_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
SOLAR_FLARE_URL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json"
PROTON_FLUX_URL = (
    "https://services.swpc.noaa.gov/json/goes/primary/" "integral-protons-1-day.json"
)
# Updated solar wind URL
SOLAR_WIND_URL = "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json"
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL")

SWPC_LINK = "https://www.swpc.noaa.gov/products-and-data"
SUN_IMAGERY_LINK = "https://sdo.gsfc.nasa.gov/data/"

# Thresholds
GEOSTORM_THRESHOLDS = {
    "Minor": 5,
    "Moderate": 6,
    "Strong": 7,
    "Severe": 8,
    "Extreme": 9,
}
FLARE_THRESHOLDS = {"M": 1e-5, "X": 1e-4}
PROTON_FLUX_THRESHOLD = 10  # pfu
SOLAR_WIND_SPEED_THRESHOLD = 600  # km/s

DAILY_SUMMARY_HOUR = 9


# Functions
def log(message):
    """Print with immediate flush"""
    logging.info(message)
    sys.stdout.flush()


def fetch_json(url):
    return requests.get(url).json()


def get_latest_kp():
    data = fetch_json(K_INDEX_URL)[-1]
    return float(data["kp_index"]), data["time_tag"]


def check_storm(kp):
    for level, threshold in sorted(GEOSTORM_THRESHOLDS.items(), key=lambda x: -x[1]):
        if kp >= threshold:
            return level
    return None


def check_flare():
    """Check for solar flares using 0.1-0.8nm band data"""
    data = fetch_json(SOLAR_FLARE_URL)
    # Filter for 0.1-0.8nm band (the one used for flare classification)
    xray_data = [d for d in data if d.get("energy") == "0.1-0.8nm"]
    if not xray_data:
        return None, None, None

    latest = xray_data[-1]
    flux = float(latest["flux"])

    for level, threshold in sorted(FLARE_THRESHOLDS.items(), key=lambda x: -x[1]):
        if flux >= threshold:
            return level, flux, latest["time_tag"]
    return None, None, None


def check_proton_flux():
    """Check proton flux for >=10 MeV energy level"""
    data = fetch_json(PROTON_FLUX_URL)
    # Filter for >=10 MeV energy level
    proton_data = [d for d in data if d.get("energy") == ">=10 MeV"]
    if not proton_data:
        return False, 0, "N/A"

    latest = proton_data[-1]
    flux = float(latest["flux"])
    return flux >= PROTON_FLUX_THRESHOLD, flux, latest["time_tag"]


def check_solar_wind():
    """Check solar wind speed with fallback for 404 errors"""
    try:
        response = requests.get(SOLAR_WIND_URL)
        if response.status_code != 200:
            log(f"Solar wind data unavailable: HTTP {response.status_code}")
            return False, 0, "N/A"

        data = response.json()
        if not data or len(data) < 2:  # First row is headers
            return False, 0, "N/A"

        # Skip header row, get latest data
        latest = data[-1]
        # Data format: [time_tag, density, speed, temperature]
        if len(latest) >= 3:
            speed = float(latest[2])  # Speed is third column
            time_tag = latest[0]
            return (speed >= SOLAR_WIND_SPEED_THRESHOLD, speed, time_tag)
        else:
            return False, 0, "N/A"
    except Exception as e:
        log(f"Solar wind data error: {e}")
        return False, 0, "N/A"


def send_slack_notification(title, message):
    payload = {
        "text": (
            f"<!channel> 🚨 *{title}*\n{message}\n"
            f"<{SWPC_LINK}|SWPC Data> | <{SUN_IMAGERY_LINK}|Solar Imagery>"
        )
    }
    requests.post(SLACK_WEBHOOK, json=payload)


def send_daily_summary():
    kp, kp_time = get_latest_kp()
    flare_level, flare_flux, flare_time = check_flare()
    proton_alert, proton_flux, proton_time = check_proton_flux()
    wind_alert, wind_speed, wind_time = check_solar_wind()
    summary = (
        f"☀️ *Daily Space Weather Summary* ({datetime.date.today()}):\n"
        f"- *Kp Index:* {kp} at {kp_time}\n"
        f"- *Solar Flare:* {flare_level or 'None'} at {flare_time or 'N/A'}\n"
        f"- *Proton Flux:* {'High' if proton_alert else 'Normal'} "
        f"({proton_flux} pfu at {proton_time})\n"
        f"- *Solar Wind:* {'Fast' if wind_alert else 'Normal'} "
        f"({wind_speed} km/s at {wind_time})"
    )
    send_slack_notification("Daily Summary", summary)


# Main Loop
if __name__ == "__main__":
    # Startup checks
    log(f"🚀 Space Weather Bot starting at {datetime.datetime.now()}")

    if not SLACK_WEBHOOK:
        log("❌ ERROR: SLACK_WEBHOOK_URL environment variable not set!")
        log("   Set it with: export SLACK_WEBHOOK_URL='your-webhook-url'")
        sys.exit(1)

    log("✅ Slack webhook configured")
    log(f"📊 Daily summaries scheduled for {DAILY_SUMMARY_HOUR}:00")
    log("🔄 Polling interval: 5 minutes")
    log("📡 Monitoring NOAA SWPC data sources...")
    log("-" * 50)

    # Test initial connection
    try:
        log("🔍 Testing NOAA API connection...")
        kp, kp_time = get_latest_kp()
        log(f"✅ Connection successful! Current Kp: {kp}")
    except Exception as e:
        log(f"❌ Failed to connect to NOAA: {e}")
        sys.exit(1)

    alerts_sent = {}
    last_summary_date = None
    check_counter = 0

    while True:
        try:
            now = datetime.datetime.now()
            check_counter += 1

            # Print status every 12 checks (1 hour)
            if check_counter % 12 == 1:
                log(f"[{now}] Check #{check_counter} - Bot running")

            # Geomagnetic Storm Alert
            kp, kp_time = get_latest_kp()
            storm_level = check_storm(kp)
            if storm_level and alerts_sent.get("storm") != storm_level:
                log(f"[{now}] 🌩️  Detected {storm_level} storm (Kp={kp})")
                send_slack_notification(
                    "Geomagnetic Storm Alert",
                    f"{storm_level} Storm (Kp {kp}) at {kp_time}",
                )
                alerts_sent["storm"] = storm_level

            # Solar Flare Alert
            flare_level, flare_flux, flare_time = check_flare()
            if flare_level and alerts_sent.get("flare") != flare_time:
                log(f"[{now}] ☀️  Detected {flare_level}-class flare")
                send_slack_notification(
                    "Solar Flare Alert",
                    f"{flare_level}-class Flare (Flux: {flare_flux}) "
                    f"at {flare_time}",
                )
                alerts_sent["flare"] = flare_time

            # Proton Event Alert
            proton_alert, proton_flux, proton_time = check_proton_flux()
            if proton_alert and alerts_sent.get("proton") != proton_time:
                log(f"[{now}] ☢️  High proton flux: {proton_flux} pfu")
                send_slack_notification(
                    "Radiation Storm Alert",
                    f"High Proton Flux: {proton_flux} pfu at {proton_time}",
                )
                alerts_sent["proton"] = proton_time

            # Solar Wind Alert
            wind_alert, wind_speed, wind_time = check_solar_wind()
            if wind_alert and alerts_sent.get("wind") != wind_time:
                log(f"[{now}] 💨 High solar wind: {wind_speed} km/s")
                send_slack_notification(
                    "Solar Wind Speed Alert",
                    f"High Solar Wind Speed: {wind_speed} km/s at {wind_time}",
                )
                alerts_sent["wind"] = wind_time

            # Daily Summary
            if now.hour == DAILY_SUMMARY_HOUR and (last_summary_date != now.date()):
                log(f"[{now}] 📊 Sending daily summary")
                send_daily_summary()
                last_summary_date = now.date()

            time.sleep(300)

        except Exception as e:
            log(f"[{now}] ❌ Error occurred: {e}")
            time.sleep(300)
