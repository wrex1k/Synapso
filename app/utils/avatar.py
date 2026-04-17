import io

from PIL import Image
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QImage, QPainter, QPainterPath, QPixmap

def rounded_pixmap(pixmap: QPixmap, size, radius: int = 20) -> QPixmap:
    """Convert a QPixmap to a rounded version with the given size and corner radius """
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

def qpixmap_to_webp_blob(
    pixmap: QPixmap,
    max_size: tuple[int, int] = (256, 256),
    quality: int = 80,
) -> bytes:
    """Convert a QPixmap to a WEBP byte blob, resizing and compressing as needed for storage."""
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

def webp_blob_to_qpixmap(blob: bytes) -> QPixmap:
    """Convert a WEBP byte blob back to a QPixmap for display."""
    qimg = QImage.fromData(QByteArray(blob), "WEBP")
    return QPixmap.fromImage(qimg)


def qpixmap_from_webp_blob_rounded(blob: bytes, size, radius: int = 20) -> QPixmap:
    """Convert a WEBP byte blob to a rounded QPixmap for display."""
    if not blob:
        return QPixmap()
    pixmap = webp_blob_to_qpixmap(blob)
    if pixmap.isNull():
        return QPixmap()
    return rounded_pixmap(pixmap, size, radius)


def restore_webp_blob_avatar(label_widget, avatar_blob: bytes, radius: int = 20) -> bool:
    """Restore a WEBP blob avatar in a QLabel widget with rounded corners."""
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