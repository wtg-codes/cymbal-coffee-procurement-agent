import os
from unittest.mock import MagicMock

import google.auth
import google.auth.credentials

os.environ["GOOGLE_CLOUD_PROJECT"] = "hackathon-y26"
os.environ["GCP_PROJECT"] = "hackathon-y26"
os.environ["CLOUDSDK_CORE_PROJECT"] = "hackathon-y26"

try:
    google.auth.default()
except Exception:
    mock_creds = MagicMock(spec=google.auth.credentials.Credentials)
    google.auth.default = lambda *args, **kwargs: (mock_creds, "hackathon-y26")
