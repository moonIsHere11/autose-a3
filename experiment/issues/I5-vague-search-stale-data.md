# search() sometimes shows data that isn't in the database

**Type:** vague

I'm using TinyDB for a small inventory script. Something weird happens: I search for some items, change a
value in the result in my code (I wasn't planning to save it, just formatting it for display), and later
when I run the same search again, the result shows my modified value even though I never called
`update()`. If I call `db.all()` the data is the old one. It feels like some caching thing.

Is this expected? It's very confusing; search should just give me what's in the database.

TinyDB 4.8, Python 3.12
