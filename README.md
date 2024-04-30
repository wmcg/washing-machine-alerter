Smart washing machine?

- i have a smart dishwasher which tell me when the dishwasher has finished - totally useless to me
- i have a washing machine that only way to alert me to the cycle being finished is agressive beeping.
- since moving it as far away as possible i no longer hear the beeping and now regularly go to fill the machine only to find that there a load from 2 days ago that has started to grow mushrooms. 
- Since i have no intention to buy a smart washing machine i plan to retro fit with this capability

Plan

1. Get a smart plug with power reading
2. Figure out approx power when idle and when running a cycle 
3. Write some pyton to send an alert to phone  using something like https://pushover.net/ to make life simple
4. [text](https://badgerbadgerbadgerbadger.dev/posts/misc/2024-04-08-is-it-dry-yet/)

- quite like the kasa stuff seems fairly cheap and has a decent python API
- bought a KP115 £27.99

```
Discovering devices on 255.255.255.255 for 3 seconds
== WashingMachine - KP115(UK) ==
	Host: 192.168.1.166
	Port: 9999
	Device state: True
	== Generic information ==
	Time:         2024-04-30 17:05:31 (tz: {'index': 39, 'err_code': 0}
	Hardware:     1.0
	Software:     1.0.20 Build 221125 Rel.092759
	MAC (rssi):   AC:15:A2:3F:BA:1B (-54)
	Location:     {'latitude': 51.5952, 'longitude': 0.0017}

	== Device specific information ==
	LED state: True
	On since: 2024-03-27 12:21:09

	== Current State ==
	<EmeterStatus power=1.864 voltage=243.664 current=0.038 total=29.797>

	== Modules ==
	+ <Module Schedule (schedule) for 192.168.1.166>
	+ <Module Usage (schedule) for 192.168.1.166>
	+ <Module Antitheft (anti_theft) for 192.168.1.166>
	+ <Module Time (time) for 192.168.1.166>
	+ <Module Cloud (cnCloud) for 192.168.1.166>
	+ <Module Emeter (emeter) for 192.168.1.166>
```

Thoughts:
1. Dont want to worry about ip changing with DHCP so will use library discovery?
2. Polling to detect when cycle is running? 5 mins ?
3. This is seemingly a legacy device (running on port 9999) which has provides more info

influx db system service
https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux_atomic_host/7/html/managing_containers/running_containers_as_systemd_services_with_podman