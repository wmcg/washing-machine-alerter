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
    if action == "start":
        message = "Washing machine cycle started!"
    elif action == "end":
        message = "Washing machine cycle ended!"
    else:
        raise Exception("action must be start or end")

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
    # idle {'power': 1.912, 'voltage': 240.948, 'current': 0.038, 'total': 29.799}
    # off {'power': 0.0, 'voltage': 243.298, 'current': 0.0, 'total': 29.8}
    while True:
        power_data = asyncio.run(get_power(device_config))
        print(f"{datetime.utcnow()} - {power_data}")
        write_influx(power_data)
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
        "power": device.emeter_realtime.power,
        "voltage": device.emeter_realtime.voltage,
        "current": device.emeter_realtime.current,
        "total": device.emeter_realtime.total,
    }


def main():
    device_config = asyncio.run(get_device_config())
    loop(device_config)


if __name__ == "__main__":
    sys.exit(main())
