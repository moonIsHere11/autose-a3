from tinydb import TinyDB, Query
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import MemoryStorage

class Counting(MemoryStorage):
    writes = 0
    def write(self, data):
        type(self).writes += 1
        super().write(data)

def mk(size):
    Counting.writes = 0
    CachingMiddleware.WRITE_CACHE_SIZE = size
    return TinyDB(storage=CachingMiddleware(Counting))

def test_batches_after_first_flush():
    old = CachingMiddleware.WRITE_CACHE_SIZE
    try:
        db = mk(5)
        for i in range(5): db.insert({'i': i})
        assert Counting.writes == 1           # first flush at 5th write
        for i in range(4): db.insert({'i': i})
        assert Counting.writes == 1           # bug: flushes on every write now
        db.insert({'i': 9})
        assert Counting.writes == 2           # second flush after 5 more writes
    finally:
        CachingMiddleware.WRITE_CACHE_SIZE = old

def test_close_flushes_remaining_and_not_more():
    old = CachingMiddleware.WRITE_CACHE_SIZE
    try:
        db = mk(3)
        for i in range(3): db.insert({'i': i})
        db.insert({'i': 3})
        before = Counting.writes
        db.close()
        assert Counting.writes == before + 1
    finally:
        CachingMiddleware.WRITE_CACHE_SIZE = old

def test_no_extra_flush_when_nothing_pending():
    old = CachingMiddleware.WRITE_CACHE_SIZE
    try:
        db = mk(2)
        db.insert({'a': 1}); db.insert({'a': 2})
        w = Counting.writes
        db.storage.flush(); db.storage.flush()
        assert Counting.writes == w
    finally:
        CachingMiddleware.WRITE_CACHE_SIZE = old

def test_data_intact(tmp_path):
    from tinydb.storages import JSONStorage
    p = str(tmp_path / 'd.json')
    old = CachingMiddleware.WRITE_CACHE_SIZE
    CachingMiddleware.WRITE_CACHE_SIZE = 3
    try:
        db = TinyDB(p, storage=CachingMiddleware(JSONStorage))
        for i in range(10): db.insert({'i': i})
        db.close()
        db = TinyDB(p)
        assert sorted(d['i'] for d in db.all()) == list(range(10))
        db.close()
    finally:
        CachingMiddleware.WRITE_CACHE_SIZE = old
