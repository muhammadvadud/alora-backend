import mimetypes

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


def validate_image_file(file: UploadedFile) -> None:
    """
    Rasmlar uchun fayl hajmi va turini tekshiradi (≤ 10MB, jpeg/png/webp).
    """
    max_size = 10 * 1024 * 1024  # 10 MB
    allowed_mimes = ["image/jpeg", "image/png", "image/webp"]

    if file.size and file.size > max_size:
        raise ValidationError("Fayl hajmi 10 MB dan oshmasligi kerak.")

    mime_type = getattr(file, "content_type", None)
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(file.name or "")

    if mime_type not in allowed_mimes:
        raise ValidationError("Faqat JPEG, PNG va WEBP formatidagi rasmlar ruxsat etiladi.")
