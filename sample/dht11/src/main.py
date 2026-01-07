import init_wlan

import ntptime
import time

import sinetstream
import json

# 割り込み処理中の例外を作成するための設定です
from machine import Timer
import micropython

# import gc

# modify
#26 GPIO20  VCC
#25 GPIO19  DATA
#24 GPIO18  NC
#23 GND     GND
import dht  # for DHT11
import machine  # for DHT11

# push_message
def push_message():
    with sinetstream.MessageWriter() as wr:
        led.value(1) # LED ON
        msg = { "time": time.gmtime() } #modify

        if init_wlan.i_am_rp2:
            # import rp2
            msg["button"] = rp2.bootsel_button()

        try:
            dht11.measure()
            temperature = dht11.temperature()
            humidity = dht11.humidity()
            print(f"Temperature: " ,temperature)
            print(f"Humidity: " ,humidity)
            msg["device"] = "DHT11"
            msg["temperature"] = temperature
            msg["humidity"] = humidity
        except OSError as e:
            print(f"Can not read sensor: {e}")
            # 失敗した場合でもキーを統一するために None (null) を設定する
            msg["device"] = "DHT11_Failed"
            msg["temperature"] = None
            msg["humidity"] = None

        s = json.dumps(msg)
        print("publish message ::  ",s)
        wr.publish(s)
        led.value(0) # LED OFF
        # gc.collect()

def timer_callback(timer):
    global timer_flag
    timer_flag = True

ntptime.server = "ntp.nict.jp" # modify

# 緊急例外バッファ用に size バイトの RAM を割り当てます(適当なサイズは約 100 バイトです)。
size=100
micropython.alloc_emergency_exception_buf(size)

print(f"start ntptime.settime host={ntptime.server}")
while True:
    try:
        print(f"before gmtime={time.gmtime()}")
        ntptime.settime()
        print(f"after  gmtime={time.gmtime()}")
        # 成功したらループを抜ける
        break
    except Exception as e:
        # 失敗したら5秒待ってリトライ
        print(f"Failed to set time, retrying...: {e}")
        time.sleep(5)
print("end ntptime.settime")



DHT11_NC = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_UP)    #  GPIO18 NC
DHT11_VCC = machine.Pin(20, machine.Pin.OUT)   #  GPIO20 VCC
DHT11_VCC.value(1) # DHT11 ON
time.sleep(1)

DHT11_DATA = machine.Pin(19, machine.Pin.IN, machine.Pin.PULL_UP)   # GPIO19 pull-up
time.sleep(1)

# Initialize DHT11 sensor on GPIO 16
dht11 = dht.DHT11(machine.Pin(19))  # GPIO19 DATA

led = machine.Pin("LED", machine.Pin.OUT)  #  onboard LED
led.value(0) # LED OFF

# タイマーを作成
timer_flag = False
timer1 = Timer()

print("start timer.") # modify

# タイマーを初期化して、周期的にコマンドラインに文字を出力する (20000ms)
# 今回は間隔を20秒に設定していますが、Micropythonの挙動で、ガベージコレクションなどが走り間隔は一定にはなりません。
timer1.init(mode=Timer.PERIODIC, period=20000, callback=timer_callback)

while True:
    if timer_flag:
        try:
            # この関数内でネットワークエラー (ECONNRESET) が
            # 発生する可能性がある
            push_message()

        except Exception as e:
            # エラーが発生してもキャッチして、コンソールに出力する
            # これでプログラムは停止しなくなる
            print(f"Failed to push message: {e}")

            # (オプション) エラー発生時にLEDを短く点滅させる
            led.value(1)
            time.sleep_ms(200) # 0.2秒点滅
            led.value(0)

        # 処理が成功しても、例外で失敗しても、
        # 必ずフラグをリセットして次のタイマー割り込みを待つ
        timer_flag = False

