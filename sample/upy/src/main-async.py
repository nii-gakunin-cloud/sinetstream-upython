import init_wlan
print("ok")

import ntptime
import time
# ntptime.host = "ntp.nict.jp"
print(f"start ntptime.settime host={ntptime.host}")
print(f"gmtime={time.gmtime()}")
ntptime.settime()
print(f"gmtime={time.gmtime()}")
print("end ntptime.settime")

import sinetstream
import time
import json
from machine import Timer
import asyncio

ev = asyncio.Event()

def ticker(timer):
    ev.set()

def publisher():
    print("start publisher")
    n = 10
    with sinetstream.MessageWriter() as wr:
        for i in range(n):
            msg = { "count": i+1,
                    "time": time.time() }
            if init_wlan.i_am_rp2:
                import rp2
                msg["button"] = rp2.bootsel_button()
            s = json.dumps(msg)
            print(f"publish {s}")
            wr.publish(s)
            ev.clear()
            await ev.wait()
    print("end publisher")

timer = Timer()
timer.init(mode=Timer.PERIODIC, period=1000, callback=ticker)
asyncio.run(publisher())

print("end main")
