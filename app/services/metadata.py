import io
import logging
from typing import Optional

from mutagen.id3 import APIC, TIT2, TPE1
from mutagen.mp3 import MP3

Cover = tuple[str, bytes]  # (mime, data)

logger = logging.getLogger(__name__)


def read_metadata(buf: io.BytesIO) -> tuple[str, str, Optional[Cover]]:
    buf.seek(0)
    audio = MP3(buf)
    title = "Unknown"
    artist = "Unknown"
    cover = None
    if audio.tags is not None:
        if "TIT2" in audio.tags:
            title = str(audio.tags["TIT2"])
        if "TPE1" in audio.tags:
            artist = str(audio.tags["TPE1"])
        apic_list = audio.tags.getall("APIC")
        if apic_list:
            cover = (apic_list[0].mime, apic_list[0].data)
            logger.info("read_metadata: found cover mime=%s size=%d", cover[0], len(cover[1]))
        else:
            logger.info("read_metadata: no APIC frames found")
    else:
        logger.info("read_metadata: no ID3 tags")
    buf.seek(0)
    return title, artist, cover


def apply_metadata(buf: io.BytesIO, title: str, artist: str, cover: Optional[Cover] = None) -> io.BytesIO:
    buf.seek(0)
    raw = buf.read()
    logger.info("apply_metadata: raw size=%d title=%s artist=%s", len(raw), title, artist)

    audio = MP3(io.BytesIO(raw))
    if audio.tags is None:
        logger.info("apply_metadata: no tags, creating new ID3")
        from mutagen.id3 import ID3
        audio.tags = ID3()

    audio.tags.add(TIT2(encoding=3, text=title))
    audio.tags.add(TPE1(encoding=3, text=artist))

    if cover:
        mime, data = cover
        logger.info("apply_metadata: cover PROVIDED mime=%s data_size=%d first_bytes=%s",
                     mime, len(data), data[:50].hex() if data else "EMPTY")
        audio.tags.delall("APIC")
        apic_before = audio.tags.getall("APIC")
        logger.info("apply_metadata: APIC after delall: %d", len(apic_before))
        audio.tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))
        apic_after = audio.tags.getall("APIC")
        logger.info("apply_metadata: APIC after add: %d data_len=%d", len(apic_after), len(apic_after[0].data) if apic_after else 0)
    else:
        logger.info("apply_metadata: cover NOT provided, keeping existing")

    out = io.BytesIO(raw)
    out.seek(0)
    audio.save(fileobj=out)
    out_size = out.tell()
    out.seek(0)
    logger.info("apply_metadata: output size=%d", out_size)

    # Verify what was saved
    verify = MP3(io.BytesIO(out.read()))
    v_apic = verify.tags.getall("APIC") if verify.tags else []
    v_tit2 = str(verify.tags.get("TIT2", "?")) if verify.tags else "?"
    logger.info("apply_metadata: verify -> title=%s APIC_count=%d", v_tit2, len(v_apic))
    if v_apic:
        logger.info("apply_metadata: verify APIC -> mime=%s data_size=%d", v_apic[0].mime, len(v_apic[0].data))
    out.seek(0)
    return out
