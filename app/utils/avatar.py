import io

from PIL import Image
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QImage, QPainter, QPainterPath, QPixmap

"""
This module provides various avatar-related utilities, such as:
- rounded_pixmap: create a rounded version of a QPixmap for display
- qpixmap_to_webp_blob: convert a QPixmap to a WEBP byte blob for storage
- webp_blob_to_qpixmap: convert a WEBP byte blob back to a QPixmap for display
"""

# convert a QPixmap to a rounded version with the given size and corner radius
def rounded_pixmap(pixmap: QPixmap, size, radius: int = 20) -> QPixmap:
    scaled = pixmap.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    rounded = QPixmap(size)
    rounded.fill(Qt.transparent)

    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)

    path = QPainterPath()
    path.addRoundedRect(0, 0, size.width(), size.height(), radius, radius)

    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled)
    painter.end()

    return rounded


# convert a QPixmap to a WEBP byte blob, resizing and compressing as needed for storage
def qpixmap_to_webp_blob(
    pixmap: QPixmap,
    max_size: tuple[int, int] = (256, 256),
    quality: int = 80,
) -> bytes:
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    pixmap.toImage().save(buf, "PNG")
    raw = bytes(buf.data())
    buf.close()

    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img.thumbnail(max_size)

    out = io.BytesIO()
    img.save(out, format="WEBP", quality=quality, method=6)
    return out.getvalue()

# convert a WEBP byte blob back to a QPixmap for display
def webp_blob_to_qpixmap(blob: bytes) -> QPixmap:
    qimg = QImage.fromData(QByteArray(blob), "WEBP")
    return QPixmap.fromImage(qimg)


# convert a WEBP byte blob to a rounded QPixmap for display (combined utility)
def qpixmap_from_webp_blob_rounded(blob: bytes, size, radius: int = 20) -> QPixmap:
    if not blob:
        return QPixmap()
    pixmap = webp_blob_to_qpixmap(blob)
    if pixmap.isNull():
        return QPixmap()
    return rounded_pixmap(pixmap, size, radius)


# restore a WEBP blob avatar in a QLabel widget with rounded corners
def restore_webp_blob_avatar(label_widget, avatar_blob: bytes, radius: int = 20) -> bool:
    if not avatar_blob:
        return False
    
    try:
        size = label_widget.size()
        pixmap = qpixmap_from_webp_blob_rounded(avatar_blob, size, radius)
        if pixmap.isNull():
            return False
        label_widget.setPixmap(pixmap)
        return True
    except Exception:
        return False