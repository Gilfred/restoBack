from uploadcenter import create_client
from uploadcenter.generated.models import PresignUploadRequest, CompleteUploadRequest
from uploadcenter.generated.api.uploads import (
    presign_upload_endpoint_v1_uploads_presign_post,
    complete_upload_endpoint_v1_uploads_complete_post
)
from fastapi import HTTPException, status
from app.core.config import settings

def get_uploadcenter_client():
    if not settings.UPLOADCENTER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clé API UploadCenter non configurée"
        )
    return create_client(
        base_url=settings.UPLOADCENTER_BASE_URL,
        token=settings.UPLOADCENTER_API_KEY
    )

def presign_upload(filename: str, size_bytes: int, mime_type: str):
    client = get_uploadcenter_client()
    request_body = PresignUploadRequest(
        project_id=settings.UPLOADCENTER_PROJECT_ID,
        filename=filename,
        size_bytes=size_bytes,
        mime_type=mime_type,
        visibility="public"  # Menu images are public
    )
    try:
        response = presign_upload_endpoint_v1_uploads_presign_post.sync(
            client=client,
            body=request_body
        )
        if not response or not hasattr(response, "upload_url"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Échec de la génération de l'URL présignée par UploadCenter"
            )
        return {
            "file_id": response.file_id,
            "upload_url": response.upload_url,
            "expires_in": response.expires_in
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur d'intégration UploadCenter presign: {str(e)}"
        )

def complete_upload(file_id: str):
    client = get_uploadcenter_client()
    request_body = CompleteUploadRequest(file_id=file_id)
    try:
        response = complete_upload_endpoint_v1_uploads_complete_post.sync(
            client=client,
            body=request_body
        )
        if not response or not hasattr(response, "id"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Échec de la confirmation de l'upload auprès d'UploadCenter"
            )
        return {
            "id": response.id,
            "url": response.url,
            "status": response.status,
            "original_name": response.original_name,
            "mime_type": response.mime_type,
            "size_bytes": response.size_bytes,
            "visibility": response.visibility
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur d'intégration UploadCenter complete: {str(e)}"
        )
