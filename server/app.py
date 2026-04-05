import os

try:
    from openenv.core.env_server.http_server import create_app
except ImportError as e:
    raise ImportError("openenv is required for the web interface.") from e

# Ensure relative imports resolve correctly based on execution context
try:
    from models import CustomerSupportAction, CustomerSupportObservation
except ImportError:
    from ..models import CustomerSupportAction, CustomerSupportObservation

from .environment import CustomerSupportEnvironment

MAX_CONCURRENT_ENVS = int(os.getenv("MAX_CONCURRENT_ENVS", "100"))

app = create_app(
    CustomerSupportEnvironment,
    CustomerSupportAction,
    CustomerSupportObservation,
    env_name="customer_support",
    max_concurrent_envs=MAX_CONCURRENT_ENVS,
)

def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
