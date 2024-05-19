import requests
import sys
import asyncio
from kasa import Discover, SmartDevice
import os
from time import sleep
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, UTC

KASA_DEVICE_ALIAS = os.environ["KASA_DEVICE_ALIAS"]  # "WashingMachine"
PUSHOVER_TOKEN = os.environ.get("PUSHOVER_TOKEN")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER")
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET")
INFLUX_ORG = os.environ.get("INFLUX_ORG")
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN")
INFLUX_URL = os.environ.get("INFLUX_URL")


def notify(action):
    if action == "START":
        message = "Washing machine cycle started!"
    elif action == "END":
        message = "Washing machine cycle ended!"
    else:
        raise Exception("action must be start or end")

    print(f"{datetime.now(UTC)} Notify action: '{action}'")
    r = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": message,
        },
        # files={"attachment": ("image.jpg", open("your_image.jpg", "rb"), "image/jpeg")},
    )

    r.raise_for_status()


def write_influx(power_data):
    client = influxdb_client.InfluxDBClient(
        url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG
    )
    write_api = client.write_api(write_options=SYNCHRONOUS)
    pd = (
        influxdb_client.Point("washing_machine_power")
        .tag("location", "basement")
        .field("power", power_data["power"])
        .field("voltage", power_data["voltage"])
        .field("current", power_data["current"])
    )
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=pd)


def device_power_status(power: float):
    # idle {'power': 1.912, 'voltage': 240.948, 'current': 0.038, 'total': 29.799}
    # off {'power': 0.0, 'voltage': 243.298, 'current': 0.0, 'total': 29.8}
    if power < 0.1:
        return "OFF"
    if power < 3.0:
        return "IDLE"
    return "ON"


def alert_on_state_change(new_state, old_state):
    if old_state == "ON" and new_state != "ON":
        notify("END")

    if old_state != "ON" and new_state == "ON":
        notify("START")


async def get_power(device_config):
    device = await SmartDevice.connect(config=device_config)
    await device.update()
    return {
        "power": device.emeter_realtime.power or 0.0,
        "voltage": device.emeter_realtime.voltage or 0.0,
        "current": device.emeter_realtime.current or 0.0,
        "total": device.emeter_realtime.total or 0.0,
    }


async def get_device_config():
    devices = await Discover.discover(discovery_timeout=5)
    for _, device in devices.items():
        await device.update()
        if device.alias == KASA_DEVICE_ALIAS:
            return device.config
    raise Exception(f"Device with alias {KASA_DEVICE_ALIAS} was not found")


def main():
    device_config = asyncio.run(get_device_config())
    print(f"{datetime.now(UTC)} Starting Loop")
    new_state = "IDLE"
    while True:
        power_data = asyncio.run(get_power(device_config))

        write_influx(power_data)

        old_state = new_state
        new_state = device_power_status(power_data["power"])
        alert_on_state_change(new_state, old_state)

        print(
            f"{datetime.now(UTC)} Power: '{power_data['power']}' Current status: '{new_state}' Old status: '{old_state}'"
        )
        sleep(60)


if __name__ == "__main__":
    sys.exit(main())
