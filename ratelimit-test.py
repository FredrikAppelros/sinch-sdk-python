import logging
import sys
import os

from sinch import Client

root = logging.getLogger()
root.setLevel(logging.INFO)
root.addHandler(logging.StreamHandler(sys.stdout))

client = Client(key_id=os.getenv("KEY_ID"), key_secret=os.getenv("KEY_SECRET"), project_id=os.getenv("PROJECT_ID"))

for i in range(10):
    client.ratelimit.httpbin()

# (1st) call httpbin (rate = 0.2 capacity = 1)
# sleep 5 seconds (1 / 0.2 = 5)
# (2nd) call httpbin - 429,

# (2nd) call httpbin - 429 (consumed the token)
