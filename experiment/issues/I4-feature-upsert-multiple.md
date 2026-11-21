# Feature request: batch upsert

**Type:** feature request

I sync records from an API into TinyDB and call `table.upsert(doc, cond)` in a loop for a few thousand
records. With `JSONStorage` this rewrites the whole file once per record and is very slow.
`insert_multiple` / `update_multiple` exist, but there's no batch version of `upsert`.

Proposal: `Table.upsert_multiple(items)` where `items` is a list of `(document, cond)` pairs, each behaving
like `upsert(document, cond)` (update matches, otherwise insert), applied in order, returning one list of
document IDs per pair. The important part for me: the whole batch should be **a single write** to the
storage.
