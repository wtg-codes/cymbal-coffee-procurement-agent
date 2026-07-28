import os
from unittest.mock import MagicMock

import google.auth
import google.auth.credentials

os.environ["GOOGLE_CLOUD_PROJECT"] = "hackathon-y26"
os.environ["GCP_PROJECT"] = "hackathon-y26"
os.environ["CLOUDSDK_CORE_PROJECT"] = "hackathon-y26"
os.environ["DISABLE_OTEL_TRACING"] = "true"

# Removed mock_creds so real GCP_CREDENTIALS can be used in integration tests

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
