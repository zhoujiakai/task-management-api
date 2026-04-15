"""API 密钥认证依赖。"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from config import cfg

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """验证 X-API-Key 请求头中的 API 密钥。"""
    if api_key != cfg.auth.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key
