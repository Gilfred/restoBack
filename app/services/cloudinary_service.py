import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, status
from app.core.config import settings

def init_cloudinary():
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )

def upload_image(file_bytes: bytes, filename: str) -> dict:
    """
    Téléverse le contenu binaire d'un fichier image vers Cloudinary (dossier 'gilexis/menu').
    Retourne un dictionnaire contenant au minimum 'url' (l'URL publique HTTPS).
    """
    init_cloudinary()
    try:
        response = cloudinary.uploader.upload(
            file_bytes,
            folder="gilexis/menu",
            resource_type="image"
        )
        secure_url = response.get("secure_url") or response.get("url")
        public_id = response.get("public_id")
        if not secure_url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Échec du téléversement vers Cloudinary: URL non retournée"
            )
        return {
            "url": secure_url,
            "public_id": public_id
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur d'intégration Cloudinary: {str(e)}"
        )

from typing import Optional

def delete_image(public_id: str):
    """
    Supprime une image sur Cloudinary à l'aide de son public_id.
    """
    if not public_id:
        return
    init_cloudinary()
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception:
        pass

def extract_public_id_from_url(url: str) -> Optional[str]:
    """
    Extrait le public_id d'une URL d'image Cloudinary si possible.
    """
    if not url or "cloudinary.com" not in url:
        return None
    try:
        parts = url.split("/upload/")
        if len(parts) < 2:
            return None
        path = parts[1]
        path_parts = path.split("/")
        if path_parts[0].startswith("v") and path_parts[0][1:].isdigit():
            path_parts = path_parts[1:]
        public_id_with_ext = "/".join(path_parts)
        public_id = public_id_with_ext.rsplit(".", 1)[0]
        return public_id
    except Exception:
        return None
