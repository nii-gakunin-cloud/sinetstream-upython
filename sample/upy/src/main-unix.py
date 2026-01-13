# main.pyからunix port版micropythonで動くように削ったもの
import sinetstream
import time
import json
n = 10
with sinetstream.MessageWriter() as wr:
    for i in range(n):
        msg = { "count": i+1,
                "time": time.time() }
        s = json.dumps(msg)
        print(f"publish {s}")
        wr.publish(s)
        time.sleep(1)
print("end main")
