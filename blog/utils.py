from django.contrib.postgres.search import (
    SearchVector,
    SearchQuery,
    SearchRank,
    SearchHeadline,
)

from blog.models import Post 

def search_post(query):
  
    # Второй вариант - для Postgres
    vector = SearchVector("title", "description", "author__username")
    search_words = SearchQuery(query)
    result = (
        Post.objects.annotate(rank=SearchRank(vector, search_words))
        .filter(rank__gt=0.001)
        .order_by("-rank")
    )

    return result
