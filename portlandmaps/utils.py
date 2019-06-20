import json
import hashlib
from datetime import datetime, timedelta

import pytz

epoch = pytz.utc.localize(datetime(1970, 1, 1, 0, 0, 0))

# This API key is embedded in portlandmaps.com and used by all visitors
public_api_key = "7D700138A0EA40349E799EA216BF82F9"


def sha256_sorted_json(stuff):
    m = hashlib.sha256()
    m.update(json.dumps(stuff, sort_keys=True).encode("utf-8"))
    return m.hexdigest()


def millis_since_epoch(dt):
    return (dt - epoch).total_seconds() * 1000
