# CachingMiddleware stops caching after the first flush

**Type:** bug report

I use `CachingMiddleware(JSONStorage)` to avoid hitting the disk on every insert. With the default
`WRITE_CACHE_SIZE` the file is written once after the first batch of writes, as expected, but after that it
looks like *every* insert writes the whole JSON file again, so after a few hundred inserts it is as slow as
not using the middleware at all. I checked by wrapping the storage and counting calls to `write()`: after the
first flush the count goes up by one for every insert.

Expected: the underlying storage is written once every `WRITE_CACHE_SIZE` writes (and on close), not on
every write.
