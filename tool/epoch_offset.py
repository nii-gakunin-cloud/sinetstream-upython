#!/usr/bin/env python3
# POSIX epochからの経過秒数を計算する
# example: python3 epoch_offset.py 2000 1 1

import datetime
import os
import sys

yyyy = int(sys.argv[1])
mm = int(sys.argv[2])
dd = int(sys.argv[3])

# POSIX epoch
t0 = datetime.datetime(year=1970, month=1, day=1,
                       hour=0, minute=0, second=0, microsecond=0,
                       tzinfo=datetime.timezone.utc).timestamp()
# print(f"t0={t0}")
assert t0 >= 0

# target epoch
t1 = datetime.datetime(year=yyyy, month=mm, day=dd,
                       hour=0, minute=0, second=0, microsecond=0,
                       tzinfo=datetime.timezone.utc).timestamp()
# print(f"t1={t1}")
assert t1 >= 0

offset = t1 - t0
offset2 = int(offset)
# print(f"offset={offset}")
print(f"offset {yyyy}-{mm}-{dd} - 1970-1-1 = {offset2}")
assert offset == offset2

# verify
cmd = f"date --date='@{offset2}' --utc --iso-8601=seconds"  # using the date command in GNU coreutils
print(cmd + "\n=> ", end="", flush=True)
os.system(cmd)
