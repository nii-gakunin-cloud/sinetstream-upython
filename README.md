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

# SINETStream for MicroPython

## ファイル構成

* src/
    * MicroPython版SINETStreamの実装
* test/
    * ユニットテスト
* tool/
    * RaspberryPi Pico W向けのスクリプト
* sample/
    * upy/
        * サンプルプログラム
* plugins/
    * broker/
        * mqtt/
            * SINETStreamのMQTTプラグイン
* lib/
    * uavro/
        * Apache AvroのMicroPython移植版
* img/
    * バイトコンパイル済みのファイル(*.mpy)
* README.md

## ビルド手順

ソースコードは `git clone --recurse .../sinetstream-upython` で取得する。
サブリポジトリとして `uavro` も取得される。


## インストール

## 依存関係にあるライブラリ

* uavro


## 利用方法

ホストはWindows 11を、
マイコンはRaspberryPi Pico Wを
想定している。
事前にマイコンにはMicroPythonがインストール(バージョンは1.26.0以降)されていると想定している。

MicroPythonインストール方法は以下を参考のこと:
- [Drag-and-Drop MicroPython](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html#drag-and-drop-micropython)
- Thonnyからインストールする方法: [Raspberry Pi Pico Workshop: Chapter 1.6 - YouTube](https://www.youtube.com/watch?v=1QqHAwCkQLU&t=62)

手順の全体像は以下のとおり:
````
    sinetstream-upython/img/〜/*.mpy
        |
        | sinetstream-upython/tool/install.bat
     ___|_________________________________________ micropython on RaspberryPi Pico W
    |   V
    | /lib/sinetstream/*.mpy
    | /lib/sinetstreamplugin/*.mpy
    | /lib/uavro/*.mpy
    | /lib/*/*.mpy
    |
    | /boot.py       # ハードウェアの設定と初期化
    | /main.py       # アプリケーション実行
    | /init_wlan.py  # WLANの初期化
    | /secret.py     # WLANのSSIDPASSWORDの指定
    | /sinetstream_config.json  # SINETStreamの設定ファイル
    |   A
    |___|_________________________________________
        |
        | sinetstream-upython/sample/upy/copy.bat
        |
    sinetstream-upython/sample/upy/*
````

### ソースコード取得

sinetstream-upythonとuavroのソースコードを取得する。

取得方法:
* githubからzipファイルをダウンロードして展開、または
* `git clone --recursive https://github.com/nii-gakunin-cloud/sinetstream-upython.git` XXX

### ツールの導入

インストールに先立って、ファイルをマイコンに転送するためのpython製のツール mpremote を導入する。

#### Python環境の導入

ホストのWindows環境を汚さないようにするためにポータブル版(Windows embeddable package (64-bit))をつかう。
ファイルは次のURLからzipファイルをダウンロードして展開する。

- https://www.python.org/ftp/python/3.12.9/python-3.12.9-embed-amd64.zip
- (https://www.python.org/downloads/windows/)

PowerShellから以下のコマンドを実行して pip を導入する。

````
cd python-3.12.9-embed-amd64
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
.\python get-pip.py
````

エディタで `python312._pth` をひらいてコメントアウトされている
`import site`
のコメントをはずす。

#### mpremote の導入

PowerShellから以下のコマンドを実行して mpremote を導入する。

````
cd python-3.12.9-embed-amd64
.\python Scripts\pip.exe install mpremote
````

mpremoteコマンドが動作するのを確認する。

````
Scripts\mpremote.exe
Connected to MicroPython at COM3
Use Ctrl-] or Ctrl-x to exit this shell
MicroPython v1.24.1 on 2024-11-29; Raspberry Pi Pico W with RP2040
Type "help()" for more information.
>>>
````

### SINETStreamのマイコンへのインストール

`sinetstream-upython\tool\install.bat` のなかにpythonとmpremoteのパスが埋め込んであるので
notepadなどのエディタで各自の環境にあわせて編集する。
そして install.bat を実行すると内部で install-deps.py と install-sinetstream.py が実行される。
install-deps.py は sinetstream の実行に必要な依存ライブラリをインターネットからダウンロードしてマイコンにインストールする。
install-sinetstream.py は `sinetstream-upython\img` にあるSINETStreamライブラリをマイコンにインストールする。

````
cd sinetstream-upython\tool
notepad install.bat
.\install.bat
````

### サンプルプログラムのインストールと実行

→[こちら](sample/upy/)

### SINETStream-upython開発者向け

空間効率・実行効率のため `.py` をバイトコンパイルして `.mpy` に変換する。
Linux環境での手順は次のとおり:

````
cd sinetstream-upython/tool
./build-mpy.sh
````

バイトコンパイルされたファイルは `sinetstream-upython/img/lib` の下に配置される。

#### mpy-cross

*.py から *.mpy にバイトコンパイルするにはmicropythonのソースコードから mpy-cross をビルドしてDockerコンテナにしている。

````
sinetstream-upython/〜/*.py
  |
  | mpy-cross <-- docker build <-- tool/Dockerfile
  V
sinetstream-upython/img/lib/〜/*.mpy
````
