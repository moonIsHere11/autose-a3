# Feature request: range query (`between`)

**Type:** feature request

To find documents with a value in a range I currently write
`(Query().age >= 18) & (Query().age <= 30)`, which is a bit verbose and easy to get wrong.
Could we have something like `Query().age.between(18, 30)` (and `where('age').between(18, 30)`)?

I'd expect both ends to be inclusive, and it should work with nested fields like
`Query().stats.score.between(1, 5)`. Documents where the field is missing, or where the value can't be
compared with the bounds (e.g. a string when the bounds are numbers), should just not match instead of
raising. It should combine with `&`, `|`, `~` like other queries.
