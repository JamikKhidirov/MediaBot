from collections import defaultdict

_history: dict[int, list[tuple[str, str, bytes]]] = defaultdict(list)
MAX = 5


def add(user_id: int, title: str, artist: str, data: bytes):
    entries = _history[user_id]
    entries.append((title, artist, data))
    if len(entries) > MAX:
        entries.pop(0)


def get_all(user_id: int) -> list[tuple[str, str, bytes]]:
    return list(_history.get(user_id, []))


def get(user_id: int, index: int) -> tuple[str, str, bytes] | None:
    entries = _history.get(user_id, [])
    if 0 <= index < len(entries):
        return entries[index]
    return None
