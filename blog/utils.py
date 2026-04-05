from django.contrib.postgres.search import (
    SearchVector,
    SearchQuery,
    SearchRank,
)

# used for searching posts on the site by post title, author, description
def search_post(query, qs):
    vector = SearchVector("title", "description", "author__username")
    search_words = SearchQuery(query)
    result = (
        qs.annotate(rank=SearchRank(vector, search_words))
        .filter(rank__gt=0.001)
        .order_by("-rank")
    )
    return result
