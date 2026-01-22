import redis.asyncio as redis
from settings.config import Config
import json
from app.cache.schemas.upload_response_schema import FileMetadataResponseModel

token_blocklist = redis.from_url(
    Config.REDIS_URL
)

async def add_jti_to_blocklist(jti: str) -> None:
    await token_blocklist.set(
        name=jti,
         value= "",
         ex= Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
async def jti_in_blocklist(jti: str) -> bool:
    msg = await token_blocklist.get(name=jti)
    return msg is not None

async def store_metadata(file_id: str, metadata: FileMetadataResponseModel):
    await token_blocklist.setex(f"file_id: {file_id}", 86400, json.dumps(metadata.model_dump(mode="json")))

async def get_stored_metadata(file_id: str) -> FileMetadataResponseModel:
    cached = await token_blocklist.get(f"file_id: {file_id}")
    return cached