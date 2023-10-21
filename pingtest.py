# continously ping a ip or hostname, recording the time the ping happened, and whether the ping succeeded or failed

from datetime import datetime
import time
from ping3 import ping

target = "ip-or-hostname-to-ping"
period = 60

while True:
    resp = ping(target)

    now = datetime.now()
    timestring = now.strftime("%Y-%m-%d %I:%M:%S %p")

    print(f"[{timestring}] ", end='')
    if resp is None:
        print("Ping Failed: Timed Out")
    elif resp is False:
        print("Ping Failed: Unknown Host")
    else:
        print(f"Ping Completed in {resp:0.1f} seconds")

    time.sleep(period)