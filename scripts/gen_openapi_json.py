"""Generate openapi.json via the command line."""

import argparse
import json
from pathlib import Path

from fastapi.openapi.utils import get_openapi

from app.utils import load_dotenv_if_not_docker

load_dotenv_if_not_docker(
    env_file=Path(__file__).parent.parent / "secret/env.example", force=True
)

from app.main import app  # noqa: E402


def write_openapi(path: Path) -> None:
    """Get OpenAPI config from FastAPI and write to file."""
    if not path.match("*.json"):
        raise ValueError("Output file must be .json") from None
    with open(path, "w") as f:
        openapi = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=app.servers,
            terms_of_service=app.terms_of_service,
            contact=app.contact,
            license_info=app.license_info,
        )
        json.dump(openapi, f, separators=(",", ":"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", dest="output", default="./openapi.json", help="output file"
    )
    args = parser.parse_args()
    write_openapi(Path(args.output))
