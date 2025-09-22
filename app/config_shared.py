import json
import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

load_dotenv(override=True)

router = APIRouter()


class SharedConfigResponse(BaseModel):
    name: str
    config_id: Optional[str]
    user_id: str
    default: bool
    settings: Optional[Dict[str, Any]]
    frontend_config: Optional[Dict[str, Any]]
    weaviate_id: str


GRAPHQL_QUERY = """
{
Get {
ELYSIA_CONFIG__(
where:{
operator: And
operands:[
{ path:["user_id"], operator: Equal, valueText:"shared" }
{ path:["default"], operator: Equal, valueBoolean:true }
]
}
limit:1
){
name
config_id
user_id
default
settings
frontend_config
_additional { id }
}
}
}
"""


def _ensure_dict(value: Any) -> Optional[Dict[str, Any]]:
    if isinstance(value, dict) or value is None:
        return value
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return None
    return None


@router.get("/config/shared", response_model=SharedConfigResponse)
def get_shared_config() -> SharedConfigResponse:
    base_url = os.getenv("WCD_URL")
    token = os.getenv("WCD_TOKEN")

    if not base_url or not token:
        raise HTTPException(status_code=500, detail="Weaviate credentials are not configured")

    graphql_endpoint = base_url.rstrip("/") + "/v1/graphql"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    try:
        response = requests.post(
            graphql_endpoint,
            json={"query": GRAPHQL_QUERY},
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Failed to query Weaviate") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Invalid response from Weaviate") from exc

    if "errors" in payload and payload["errors"]:
        raise HTTPException(status_code=502, detail="Weaviate returned errors")

    configs = (
        payload.get("data", {})
        .get("Get", {})
        .get("ELYSIA_CONFIG__", [])
    )

    if not configs:
        raise HTTPException(status_code=404, detail="Shared default config not found")

    config = configs[0]

    return SharedConfigResponse(
        name=config.get("name", ""),
        config_id=config.get("config_id"),
        user_id=config.get("user_id", ""),
        default=bool(config.get("default", False)),
        settings=_ensure_dict(config.get("settings")),
        frontend_config=_ensure_dict(config.get("frontend_config")),
        weaviate_id=config.get("_additional", {}).get("id", ""),
    )
