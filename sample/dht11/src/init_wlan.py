import network
import time


def check_rp2():
    try:
        import rp2
        return True
    except:
        return False

i_am_rp2 = check_rp2()

def wlan_status(wlan, st=None):
    if st is None:
        st = wlan.status()
    m = {
        network.STAT_IDLE: "STAT_IDLE",
        network.STAT_CONNECTING: "STAT_CONNECTING", 
        network.STAT_WRONG_PASSWORD: "STAT_WRONG_PASSWORD",
        network.STAT_NO_AP_FOUND: "STAT_NO_AP_FOUND",
        network.STAT_CONNECT_FAIL: "STAT_CONNECT_FAIL", 
        network.STAT_GOT_IP: "STAT_GOT_IP",
    }
    if i_am_rp2:
        # Connecting to the Internet with Raspberry Pi Pico W-series
        # https://datasheets.raspberrypi.com/picow/connecting-to-the-internet-with-pico-w.pdf
        # 3.6.1. Connection status codes
        # The values returned by the wlan.status() call are defined in the CYW43 wireless driver,
        # and are passed directly through to user-code.
        #
        # https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html says:
        # Raspberry Pi Pico W and Raspberry Pi Pico 2 W use the Infineon CYW43439.
        #
        # The values are defined in https://github.com/georgerobotics/cyw43-driver/blob/main/src/cyw43.h.
        m |= {
            0:  "CYW43_LINK_DOWN",    # link is down
            1:  "CYW43_LINK_JOIN",    # Connected to wifi
            2:  "CYW43_LINK_NOIP",    # Connected to wifi, but no IP address
            3:  "CYW43_LINK_UP",      # Connect to wifi with an IP address
            -1: "CYW43_LINK_FAIL",    # Connection failed
            -2: "CYW43_LINK_NONET",   # No matching SSID found (could be out of range, or down)
            -3: "CYW43_LINK_BADAUTH",  # Authenticatation failure
        }
    return m.get(st, f"{st}")

def init_wlan(ssid, password):
    print("start init_wlan")
    wlan = network.WLAN(network.STA_IF)
    print("activate wlan")
    wlan.active(True)
    if wlan.isconnected():
        print("already connected")
    else:
        wlan.connect(ssid, password)
        print("connecting")
        while True:
            st = wlan.status()
            print(f"wlan.status={wlan_status(wlan, st)}")
            if st == network.STAT_GOT_IP:
                break
            time.sleep(1)
        print(f"wlan.status.rssi={wlan.status("rssi")}")
        print("connected")
    print("end init_wlan")
    return wlan

def stop_wlan():
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(False)

def show_ipconfig(wlan, p):
    try:
        print(f"wlan.ipconfig.{p}={wlan.ipconfig(p)}")
    except Exception:
        pass
def show_config(wlan, p):
    try:
        v = wlan.config(p)
        if p == "pm":
            v = { network.WLAN.PM_PERFORMANCE: "PM_PERFORMANCE",
                  network.WLAN.PM_POWERSAVE: "PM_POWERSAVE",
                  network.WLAN.PM_NONE: "PM_NONE" }[v]
        print(f"wlan.config.{p}={str1(v)}")
    except Exception:
        pass
def str1(x):
    return x.hex(":") if isinstance(x, bytes) else x

import secret
wlan = init_wlan(secret.WLAN_SSID, secret.WLAN_PASSWORD)
print(f"wlan.ifconfig={wlan.ifconfig()}")

for p in ["dhcp4", "gw4", "dhcp6", "autoconf6", "addr4", "addr6", "dns", "prefer"]:
    show_ipconfig(wlan, p)
for p in ["mac", "ssid", "channel", "hidden", "security", "key", "hostname", "reconnects", "txpower", "pm"]:
    show_config(wlan, p)
#print(f"country={wlan.country()}")
#print(f"hostname={wlan.hostname()}")
