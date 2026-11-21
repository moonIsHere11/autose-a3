"""Hidden acceptance tests for I5 (vague): mutating search results must not change later results."""
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage


def mk():
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple([{'item': 'bolt', 'qty': 5}, {'item': 'nut', 'qty': 7}])
    return db


def test_mutating_search_result_does_not_leak_into_next_search():
    db = mk(); q = Query()
    r = db.search(q.item == 'bolt')
    r[0]['qty'] = 999
    assert db.search(q.item == 'bolt')[0]['qty'] == 5


def test_mutating_nested_value_does_not_leak():
    db = TinyDB(storage=MemoryStorage); q = Query()
    db.insert({'item': 'bolt', 'tags': ['a']})
    db.search(q.item == 'bolt')[0]['tags'].append('b')
    assert db.search(q.item == 'bolt')[0]['tags'] == ['a']


def test_results_still_cached_and_doc_ids_kept():
    db = mk(); q = Query()
    cond = q.item == 'nut'
    r1 = db.search(cond)
    assert cond in db.table('_default')._query_cache
    assert db.search(cond)[0].doc_id == r1[0].doc_id == 2


def test_update_still_visible_to_search():
    db = mk(); q = Query()
    db.search(q.item == 'bolt')
    db.update({'qty': 1}, q.item == 'bolt')
    assert db.search(q.item == 'bolt')[0]['qty'] == 1
