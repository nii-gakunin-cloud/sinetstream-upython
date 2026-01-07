#!/usr/bin/env python3

import mpremote.main

from pathlib import Path
import json
import sys

config = json.load(open("config.json"))

top_dir = config.get("top_dir")
assert Path(top_dir, "package.json").is_file()
# img_dir = config.get("img_dir")
# assert Path(img_dir).is_dir()
lib_dir = config.get("lib_dir")
assert Path(lib_dir).is_dir()


def mpremote1(args):
    save_sys_argv = sys.argv
    sys.argv = ["mpremote"] + args.split()
    res = mpremote.main.main()
    assert res == 0, "mpremote failure"
    sys.argv = save_sys_argv


# mpremote1("fs mkdir :/lib")
mpremote1(f"fs cp -r {lib_dir} :/")
