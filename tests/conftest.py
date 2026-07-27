import os
from unittest.mock import MagicMock

import google.auth
import google.auth.credentials

os.environ["GOOGLE_CLOUD_PROJECT"] = "hackathon-y26"
os.environ["GCP_PROJECT"] = "hackathon-y26"
os.environ["CLOUDSDK_CORE_PROJECT"] = "hackathon-y26"
os.environ["DISABLE_OTEL_TRACING"] = "true"

# Mock google.auth.default to prevent DefaultCredentialsError or GCP API calls in CI
mock_creds = MagicMock(spec=google.auth.credentials.Credentials)
google.auth.default = lambda *args, **kwargs: (mock_creds, "hackathon-y26")

# Mock google.cloud.logging.Client
try:
    import google.cloud.logging

    google.cloud.logging.Client = MagicMock()
except ImportError:
    pass

# Mock google.adk.telemetry.google_cloud.get_gcp_exporters
try:
    import google.adk.telemetry.google_cloud

    google.adk.telemetry.google_cloud.get_gcp_exporters = lambda *args, **kwargs: []
except (ImportError, AttributeError):
    pass
