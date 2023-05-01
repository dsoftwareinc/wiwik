# Search

## Integration with Meilisearch

wiwik can integrate with [Meilisearch](https://www.meilisearch.com/).
In order to integrate with meilisearch, you need to set up three environment
variables:

```shell
MEILISEARCH_ENABLED=TRUE
MEILISEARCH_SERVER_ADDRESS=http://localhost:7700
MEILISEARCH_MASTERKEY=masterKey
```

In order to populate the index, run

```shell
python manage.py run_job populate_meilisearch
```

The document gets updated when a question is saved.

## Using postgres full-text-search

There are two levels of search when using postgres database search.  
The first level of search is implemented as an extension to the `Post` model:
There is a field `search_vector` which is updated when saving a post.

The calculation of search vector uses postgres full text search with:

- Post title with weight `A`.
- Post content with weight `B`.
- Post tags with weight `C`.
- Answers content with weight `D`.

Once a user submits a search, it runs a postgres search query on that vector and
ranks results accordingly.

The second level of search, if there are no results from the first level -
involves calculating trigram distance between the query and the post body (i.e.,
title+content).

## Using sqlite

When using sqlite, the search method is simply looking in the post title for a
match.
