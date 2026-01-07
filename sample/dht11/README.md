<!--
Copyright (C) 2025 National Institute of Informatics

Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# sinetstream-upythonをつかった温湿度センサーWriterのサンプルプログラム

## 概要

<!---
````
         +--マイコン-------------+
         | +--MicroPython-------+|
         | |   +-------------+  ||
[DHT11]--| |   | main.py     |  ||
         | |   +-------------+  ||
         | |   | SINETStream |-------WiFi---[アクセスポイント]---[MQTTブローカ]
         | |   +-------------+  ||
         | +--------------------+|
         +-----------------------+
````
--->

RaspberryPi Pico Wにつないだ温湿度センサーモジュールDTH11をつかって20秒間隔で温湿度を測定しMQTTブローカーに送信するプログラムである。
受信は簡単のためPCにインストールしたsinetstream_cliを利用する。

````mermaid
graph LR
  subgraph RP2[RaspberryPi Pico W]
    subgraph upy[MicroPython]
      main.py---SINETStream---sinetstream_config.json
      main.py---secret.py
    end
    RTC([RTC])
    bootsel([bootsel button])
    STA
    main.py-.-RTC
    main.py-.-bootsel
  end
  AP
  inet((Internet))
  mqtt[MQTT Broker]
  ntp[Time Server]
  subgraph PC
    cli[sinetstream_cli]
  end
  DHT11===|GPIO|RP2
  DHT11---main.py
  SINETStream-.-STA
  STA-.WiFi.-AP
  AP-.-inet
  inet-.-mqtt
  inet-.-ntp
  SINETStream--publish-->mqtt
  mqtt--subscribe-->cli
  %%main.py-->ntp
  RTC--ntp-->ntp
````
| 用語 | 説明 |
|---|---|
| main.py | MicroPythonでのメインルーチン |
| SINETStream | MicroPython版SINETStream |
| sinetstream_config.json | SINETStreamの設定ファイル |
| secret.py | WiFiのSSID/Passwordの設定ファイル |
| bootsel button | RaspberryPi Pico W上のbootselボタン |
| STA | Station(WiFi端末) |
| RTC | Real Time Clock(内蔵時計) |
| AP | Access Point(WiFi基地局) |
| MQTT Broker | sinetstream_config.jsonで指定されているMQTTブローカー |
| sinetstream_cli | SINETStreamを簡易的に利用するコマンド(Python/Java) |
| Time Server | RaspberryPi Picoの時刻合わせに利用するNTPサーバー(main.pyで指定) |


## ファイル構成

* README.md
* src/
    * boot.py
        * マイコンの/boot.pyのサンプル
        * 中身は空
    * main.py
        * マイコンの/main.pyのサンプル
        * init_wlanを実行してネットワークが使えるようになったらNTPで時刻合わせをして、Writerをつくって現在時刻を10回送信して終了する。
        * Raspberry Pi Picoの場合はbootselボタンの状態も付けて送信する。
    * init_wlan.py
        * WLANの初期化してDHCPでネットワークを設定する。
    * secret.py
        * WLAN接続のためのSSIDとPASSWORD設定
    * sinetstream_config.json
        * Writerのパラメータ
        * topic, brokers は環境にあわせて変更する。

## 設定

DHT11はRaspberryPi Pico WのGPIOに接続する。
接続するピンはmain.pyで下記の表の結線を想定してハードコーディングしているので実配線にあわせた変更が必要であろう。

| RasPi Pico W | DHT11 |
|---|---|
| pin26 GPIO20 | pin1 VCC |
| pin25 GPIO19 | pin2 DATA |
| pin24 GPIO18 | pin3 NC |
| pin23 GND    | pin4 GND |

`src/secret.py` を編集して利用するWiFiのSSIDとパスワードを設定する。

特定のNTPサーバーを利用したい場合は `main.py` で `ntptime.host =` の行で設定する。

`src/sinetstream_config.json` を編集してSINETStreamの設定をする。`brokers` や `topic` は利用環境にあわせた設定が必要であろう。

## マイコンへのインストール

ホストはWindows 11を、
マイコンはRaspberryPi Pico WまたはRaspberryPi Pico 2 Wを
想定している。

````
cd sinetstram-upython\sample\upy
.\copy.bat
````

> 注意:
> MicroPythonはバージョン1.25.0以下ではボタンの状態を正しく取得できず常に1になる問題がある。
> バージョン1.26.1以降で問題が解消されている。

## マイコンでの実行

`mpremote repl` でマイコン上のMicroPythonインタプリタに接続して、
Ctrl-Dでソフトリセットをかけるとmain.pyから実行される。
インタプリタから抜けるには Ctrl-] か Ctrl-X を押す。

````
PS C:\Users\koie\repo\sinetstream-upython\sample\upy> ./repl.bat
Use Ctrl-D to soft reboot
Connected to MicroPython at COM4
Use Ctrl-] or Ctrl-x to exit this shell
<<<ここでCtrl-Dを押す>>>

start init_wlan
activate wlan
already connected
end init_wlan
wlan.ifconfig=('192.168.###.121', '255.255.255.0', '192.168.###.1', '8.8.8.8')
wlan.ipconfig.dhcp4=True
wlan.ipconfig.gw4=192.168.###.1
wlan.ipconfig.autoconf6=True
wlan.ipconfig.addr4=('192.168.###.121', '255.255.255.0')
wlan.ipconfig.addr6=[('#############', 48, 0, 0), (########', 48, ######, ########)]
wlan.config.mac=##:##:##:##:##:##
wlan.config.ssid=#############
wlan.config.channel=#
wlan.config.security=#########
wlan.config.hostname=Pico2W
wlan.config.txpower=31
wlan.config.pm=PM_PERFORMANCE
start ntptime.settime host=ntp.nict.jp
before gmtime=(2025, 10, 22, 5, 34, 29, 2, 295)
after  gmtime=(2025, 10, 22, 5, 34, 29, 2, 295)
end ntptime.settime
start timer.
Temperature:　 27
Humidity:  32
publish message ::   {"time": [2025, 10, 22, 5, 35, 9, 2, 295], "device": "DHT11", "button": 0, "humidity": 32, "temperature": 27}
Temperature:　 27
Humidity:  32
publish message ::   {"time": [2025, 10, 22, 5, 35, 25, 2, 295], "device": "DHT11", "button": 0, "humidity": 32, "temperature": 27}

````

PC上で `sinetstream_cli` をつかうと、このサンプルプログラムが送信したメッセージを受信できる。
実行例:
````
$ sinetstream_cli read -nc type=mqtt brokers=broker.emqx.io:1883 topic=sinetstream-upython-test
````
venv環境をつくってsinetstream_cliをインストールし実行する例:
````
$ make
python3 -m venv venv
venv/bin/python -m pip install sinetstream_cli
...
cp src/sinetstream_config.json venv/.sinetstream_config.yml
cd venv && bin/sinetstream_cli read --text
````

Windows PCに `sinetstream_cli` をインストールする手順は[こちら](https://github.com/nii-gakunin-cloud/sinetstream/tree/main/python/sample/cli/README.md#windows環境でpython版をインストール)を参照のこと。
