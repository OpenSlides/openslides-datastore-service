import os
import sys

import requests

from datastore.shared.flask_frontend import build_url_prefix, get_health_url


MODULE = os.environ["MODULE"]
PORT = os.environ["PORT"]

prefix = build_url_prefix(MODULE)
path = get_health_url(prefix)
url = f"http://localhost:{PORT}{path}"

response = requests.get(url)
if response.status_code != 200:
    sys.exit(1)
