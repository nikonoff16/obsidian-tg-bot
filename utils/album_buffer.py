# utils/album_buffer.py
from collections import defaultdict
from datetime import datetime

class AlbumBuffer:
    """
    Копит сообщения альбома по media_group_id,
    отстреливает callback, когда спустя timeout новых частей нет.
    """
    def __init__(self, cb_save, timeout=1.0, context=None):
        self._groups = defaultdict(list)          # id -> [messages]
        self._cb_save = cb_save                   # coro(messages)
        self._timeout = timeout                   # сек.
        self._tasks = {}                          # id -> asyncio.Handle
        self._context = context

    def add(self, message, loop):
        gid = message.media_group_id
        self._groups[gid].append(message)

        # сдвигаем таймер
        if gid in self._tasks:
            self._tasks[gid].cancel()
        self._tasks[gid] = loop.call_later(
            self._timeout,
            lambda: loop.create_task(self._flush(gid))
        )

    async def _flush(self, gid):
        msgs = self._groups.pop(gid, [])
        self._tasks.pop(gid, None)
        if msgs:
            await self._cb_save(msgs, self._context)  # 👈 передаём context
