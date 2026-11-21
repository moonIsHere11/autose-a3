import pytest
from tinydb import TinyDB, Query, where
from tinydb.storages import MemoryStorage

def mk():
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple([{'age': 17}, {'age': 18}, {'age': 25}, {'age': 30}, {'age': 31},
                        {'age': 'x'}, {'name': 'n'}, {'age': None}])
    return db

def test_inclusive_bounds_and_where():
    db = mk()
    assert sorted(d['age'] for d in db.search(Query().age.between(18, 30))) == [18, 25, 30]
    assert len(db.search(where('age').between(18, 30))) == 3

def test_nested_missing_incomparable():
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple([{'stats': {'score': 1}}, {'stats': {'score': 5}}, {'stats': {'score': 6}},
                        {'stats': 3}, {'stats': {'score': 'hi'}}, {}])
    assert len(db.search(Query().stats.score.between(1, 5))) == 2

def test_combine():
    db = mk(); q = Query()
    assert len(db.search(q.age.between(18, 30) & q.age.between(25, 40))) == 2
    assert len(db.search(q.age.between(0, 17) | q.age.between(31, 99))) == 2
    assert len(db.search(~q.age.between(18, 30))) == 5   # 17, 31, 'x', missing, None

def test_cache_correct_and_hash_distinct():
    db = mk(); q = Query()
    assert len(db.search(q.age.between(18, 25))) == 2
    assert len(db.search(q.age.between(18, 30))) == 3
    assert len(db.search(q.age.between(18, 25))) == 2
    assert hash(q.age.between(1, 2)) != hash(q.age.between(1, 3))
    assert q.age.between(1, 2).is_cacheable()
