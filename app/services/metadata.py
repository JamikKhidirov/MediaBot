import io
from typing import Optional

from mutagen.id3 import APIC, TIT2, TPE1
from mutagen.mp3 import MP3

Cover = tuple[str, bytes]  # (mime, data)


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
        if "APIC" in audio.tags:
            cover = (audio.tags["APIC"].mime, audio.tags["APIC"].data)
    buf.seek(0)
    return title, artist, cover


def apply_metadata(buf: io.BytesIO, title: str, artist: str, cover: Optional[Cover] = None):
    buf.seek(0)
    audio = MP3(buf)
    if audio.tags is None:
        from mutagen.id3 import ID3
        audio.tags = ID3()
    # Remove old cover if exists
    if "APIC" in audio.tags:
        del audio.tags["APIC"]
    audio.tags.add(TIT2(encoding=3, text=title))
    audio.tags.add(TPE1(encoding=3, text=artist))
    if cover:
        mime, data = cover
        audio.tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))
    audio.save(fileobj=buf)
    buf.seek(0)
