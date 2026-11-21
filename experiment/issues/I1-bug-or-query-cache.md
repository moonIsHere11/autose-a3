# Wrong results when I run an OR query after an AND query

**Type:** bug report

I have a table with `a` and `b` fields. If I first search with `(Query().a == 1) & (Query().b == 1)` and then
with `(Query().a == 1) | (Query().b == 1)`, the second search returns only the one document from the first
search instead of the three documents that match. If I restart Python and run only the OR query, I get 3
results as expected. Single conditions (without `&` / `|`) seem fine.

```python
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage
db = TinyDB(storage=MemoryStorage)
db.insert_multiple([{'a': 1, 'b': 1}, {'a': 1, 'b': 0}, {'a': 0, 'b': 1}, {'a': 0, 'b': 0}])
q = Query()
print(len(db.search((q.a == 1) & (q.b == 1))))  # 1, correct
print(len(db.search((q.a == 1) | (q.b == 1))))  # prints 1, expected 3
```
TinyDB from master, Python 3.12.
