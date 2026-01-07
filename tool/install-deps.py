#!/usr/bin/env python3

import mpremote.main

from pathlib import Path
import json
import sys

config = json.load(open("config.json"))
top_dir = config.get("top_dir")
package_json = Path(top_dir, "package.json")


def mpremote1(argv):
    save_sys_argv = sys.argv
    sys.argv = ["mpremote"] + argv
    res = mpremote.main.main()
    assert res == 0, "mpremote failure"
    sys.argv = save_sys_argv


mpremote1(["mip", "install"] + [f"{x[0]}@{x[1]}" for x in json.loads(open(package_json).read())["deps"]])
