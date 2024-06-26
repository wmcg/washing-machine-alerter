import requests
import sys
import asyncio
from kasa import Discover, SmartDevice
import os
from time import sleep
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

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

    print(f"{datetime.utcnow()} Notify action: '{action}'")
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


def loop(device_config):
    current_status = "IDLE"
    while True:
        power_data = asyncio.run(get_power(device_config))
        write_influx(power_data)

        old_status = current_status
        current_status = device_power_status(power_data["power"])

        if old_status == "ON" and current_status == "IDLE":
            notify("END")

        if old_status == "IDLE" and current_status == "ON":
            notify("START")

        print(
            f"{datetime.utcnow()} Power: '{power_data['power']}' Current status: '{current_status}' Old status: '{old_status}'"
        )
        sleep(60)


async def get_device_config():
    devices = await Discover.discover(discovery_timeout=5)
    for ip, device in devices.items():
        await device.update()
        if device.alias == KASA_DEVICE_ALIAS:
            return device.config
    raise Exception(f"Device with alias {KASA_DEVICE_ALIAS} was not found")


async def get_power(device_config):
    device = await SmartDevice.connect(config=device_config)
    await device.update()
    return {
        "power": device.emeter_realtime.power or 0.0,
        "voltage": device.emeter_realtime.voltage or 0.0,
        "current": device.emeter_realtime.current or 0.0,
        "total": device.emeter_realtime.total or 0.0,
    }


def device_power_status(power: float):
    # idle {'power': 1.912, 'voltage': 240.948, 'current': 0.038, 'total': 29.799}
    # off {'power': 0.0, 'voltage': 243.298, 'current': 0.0, 'total': 29.8}
    if power < 0.1:
        return "OFF"
    if power < 3.0:
        return "IDLE"
    return "ON"


def main():
    device_config = asyncio.run(get_device_config())
    loop(device_config)


if __name__ == "__main__":
    sys.exit(main())
