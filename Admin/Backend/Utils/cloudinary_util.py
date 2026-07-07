"""
Cloudinary — upload foto produk & foto profil.
File diterima Flask sebagai FileStorage (request.files['foto']),
lalu stream langsung ke Cloudinary tanpa disimpan ke disk server.
"""
import cloudinary
import cloudinary.uploader
from config import Config

cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET,
    secure=True,
)


def upload_image(file_storage, folder):
    """
    file_storage: werkzeug FileStorage (dari request.files['foto'])
    Mengembalikan dict {"url": ..., "public_id": ...}
    """
    result = cloudinary.uploader.upload(
        file_storage,
        folder=folder,
        resource_type="image",
        transformation=[{"width": 800, "height": 800, "crop": "limit", "quality": "auto"}],
    )
    return {"url": result.get("secure_url"), "public_id": result.get("public_id")}


def delete_image(public_id):
    if not public_id:
        return
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception as err:
        print(f"[Cloudinary] Gagal hapus gambar lama: {err}")
