from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

def mk():
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple([{'a': 1, 'b': 1}, {'a': 1, 'b': 0}, {'a': 0, 'b': 1}, {'a': 0, 'b': 0}])
    return db

def test_and_then_or():
    db = mk(); q = Query()
    assert len(db.search((q.a == 1) & (q.b == 1))) == 1
    assert len(db.search((q.a == 1) | (q.b == 1))) == 3

def test_or_then_and():
    db = mk(); q = Query()
    assert len(db.search((q.a == 1) | (q.b == 1))) == 3
    assert len(db.search((q.a == 1) & (q.b == 1))) == 1

def test_hashes_differ_and_cacheable():
    q = Query()
    x, y = (q.a == 1), (q.b == 1)
    assert hash(x & y) != hash(x | y)
    assert (x | y).is_cacheable() and (x & y).is_cacheable()
    assert (x | y) == (y | x)

def test_cache_still_used():
    db = mk(); q = Query()
    cond = (q.a == 1) | (q.b == 1)
    db.search(cond)
    assert cond in db.table('_default')._query_cache
