from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from spaik_sdk.attachments.storage.base_file_storage import BaseFileStorage
from spaik_sdk.server.authorization.base_authorizer import BaseAuthorizer
from spaik_sdk.server.authorization.base_user import BaseUser
from spaik_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class FileUploadResponse(BaseModel):
    file_id: str
    mime_type: str
    filename: Optional[str]
    size_bytes: int


class FileDeleteResponse(BaseModel):
    success: bool


class FileRouterFactory:
    def __init__(
        self,
        file_storage: BaseFileStorage,
        authorizer: Optional[BaseAuthorizer[BaseUser]] = None,
    ):
        self.file_storage = file_storage
        self.authorizer = authorizer

    def create_router(self, prefix: str = "/files") -> APIRouter:
        router = APIRouter(prefix=prefix, tags=["files"])

        async def get_current_user(request: Request) -> BaseUser:
            if self.authorizer is None:
                return BaseUser("anonymous")
            user = await self.authorizer.get_user(request)
            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")
            return user

        @router.post("", response_model=FileUploadResponse)
        async def upload_file(
            file: UploadFile = File(...),
            user: BaseUser = Depends(get_current_user),
        ):
            if self.authorizer and not await self.authorizer.can_upload_file(user):
                raise HTTPException(status_code=403, detail="Not authorized to upload files")

            content = await file.read()
            mime_type = file.content_type or "application/octet-stream"

            metadata = await self.file_storage.store(
                data=content,
                mime_type=mime_type,
                owner_id=user.get_id(),
                filename=file.filename,
            )

            return FileUploadResponse(
                file_id=metadata.file_id,
                mime_type=metadata.mime_type,
                filename=metadata.filename,
                size_bytes=metadata.size_bytes,
            )

        @router.get("/{file_id}")
        async def download_file(
            file_id: str,
            user: BaseUser = Depends(get_current_user),
        ):
            metadata = await self.file_storage.get_metadata(file_id)
            if metadata is None:
                raise HTTPException(status_code=404, detail="File not found")

            if self.authorizer and not await self.authorizer.can_read_file(user, metadata):
                raise HTTPException(status_code=403, detail="Not authorized to access this file")

            try:
                content, _ = await self.file_storage.retrieve(file_id)
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail="File not found")

            return Response(
                content=content,
                media_type=metadata.mime_type,
                headers={
                    "Content-Disposition": f'inline; filename="{metadata.filename or file_id}"',
                },
            )

        @router.delete("/{file_id}", response_model=FileDeleteResponse)
        async def delete_file(
            file_id: str,
            user: BaseUser = Depends(get_current_user),
        ):
            metadata = await self.file_storage.get_metadata(file_id)
            if metadata is None:
                raise HTTPException(status_code=404, detail="File not found")

            if self.authorizer and not await self.authorizer.can_delete_file(user, metadata):
                raise HTTPException(status_code=403, detail="Not authorized to delete this file")

            success = await self.file_storage.delete(file_id)
            return FileDeleteResponse(success=success)

        return router
