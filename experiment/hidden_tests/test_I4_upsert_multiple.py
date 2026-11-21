from tinydb import TinyDB, Query
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import MemoryStorage
from tinydb.table import Document

class Counting(MemoryStorage):
    writes = 0
    def write(self, data):
        type(self).writes += 1
        super().write(data)

def mk():
    Counting.writes = 0
    return TinyDB(storage=Counting)

def test_basic_update_and_insert():
    db = mk(); q = Query()
    db.insert_multiple([{'n': 'a', 'v': 1}, {'n': 'b', 'v': 1}])
    ids = db.upsert_multiple([({'n': 'a', 'v': 2}, q.n == 'a'),
                              ({'n': 'c', 'v': 3}, q.n == 'c'),
                              ({'v': 9}, q.n == 'b')])
    assert sorted(d['v'] for d in db.all()) == [2, 3, 9]
    assert [d['n'] for d in db.all()] == ['a', 'b', 'c']
    assert len(ids) == 3 and ids[0] == [1] and ids[1] == [3] and ids[2] == [2]

def test_single_write_and_doc_id_documents():
    db = mk(); q = Query()
    db.insert({'n': 'x', 'v': 0})
    Counting.writes = 0
    db.upsert_multiple([({'n': 'x', 'v': 1}, q.n == 'x'),
                        ({'n': 'y', 'v': 2}, q.n == 'y'),
                        (Document({'n': 'z', 'v': 3}, doc_id=1), None),
                        ({'n': 'w', 'v': 4}, q.n == 'w')])
    assert Counting.writes == 1
    assert db.get(doc_id=1)['v'] == 3

def test_cache_and_ids_consistent():
    db = mk(); q = Query()
    db.insert({'n': 'a', 'v': 1})
    assert db.search(q.v == 1) != []          # populate query cache
    db.upsert_multiple([({'n': 'a', 'v': 2}, q.n == 'a'), ({'n': 'b', 'v': 1}, q.n == 'b')])
    assert [d['n'] for d in db.search(q.v == 1)] == ['b']
    assert db.insert({'n': 'c'}) == 3         # ids continue after batch inserts

def test_caching_middleware_counts_one_write():
    old = CachingMiddleware.WRITE_CACHE_SIZE
    CachingMiddleware.WRITE_CACHE_SIZE = 3
    try:
        Counting.writes = 0
        db = TinyDB(storage=CachingMiddleware(Counting)); q = Query()
        db.upsert_multiple([({'k': i}, q.k == i) for i in range(10)])
        assert Counting.writes == 0     # 1 cached write, far below the flush threshold
        db.close()
        assert Counting.writes == 1
    finally:
        CachingMiddleware.WRITE_CACHE_SIZE = old
