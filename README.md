# django-queryhunter
Hunt down the lines of your Django application code which are responsible for executing the most queries.

Libraries such as [django-silk](https://github.com/jazzband/django-silk) are excellent for profiling the queries 
executed by your Django application. We have found, however, that they do not provide a completely straightforward
way to identify the lines of your **application** code which are responsible for executing the most queries.
This library aims to fill that gap by providing a simple code-first approach to query profiling. 
One particularly useful feature of this view of profiling is quickly identifying missing `select_related` and `prefetch_related` calls.

## Highlights

- Context manager and middleware for profiling queries which can provide a detailed report of the lines of your 
  application code which are responsible for executing SQL queries, including data on:
  - The module name and the line number of the code which executed the query.
  - The executing code itself on that line.
  - The number of times that line was responsible for executing a query.
  - The SQL query itself. Note that we only display the _last_ SQL query executed on that line.
- Configurable options for filtering, sorting, printing or logging the results.
- Lightweight and easy to use.

## Installation
```bash
pip install django-queryhunter
```

You must then declare the `QUERYHUNTER_BASE_DIR` setting in your settings.py file. This is 
the way that queryhunter knows where to look for your application code. You can use the built-in callable
`queryhunter.default_base_dir` to set it to be the project root or make it a string of your choosing.

```python
import queryhunter

QUERYHUNTER_BASE_DIR = queryhunter.default_base_dir()
```

## Usage via Example

Let's suppose we have a Django application with the following models (a fully functional example can be found in the
`queryhunter.tests` directory):

```python
# queryhunter/tests/models.py
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)

class Post(models.Model):
    content = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
```

Now suppose we have another module `my_module.py` where we create an author and then create
5 posts for that author. We then collect the authors name in a list (this code is clearly
contrived, but it serves to illustrate a point). We run this code under the 
`queryhunter.queryhunter` context manager:

```python
# queryhunter/tests/my_module.py
from queryhunter.tests.models import Post, Author
from queryhunter import queryhunter

def create_posts_and_collect_authors() -> list[Author]:
    with queryhunter():
        author = Author.objects.create(name='Billy')
        for i in range(5):
            Post.objects.create(content=f'content {i}', author=author)
        authors = []
        posts = Post.objects.all()
        for post in posts:
            authors.append(post.author.name)
    return authors
```

Let's now run the code

```python
>>> from queryhunter.tests.my_module import create_posts_and_collect_authors
>>> create_posts_and_collect_authors()
```
and see what the output from the queryhunter is:

```bash
queryhunter/tests/my_module.py
====================================
Line no: 7 | Code: author = Author.objects.create(name='Billy') | Num. Queries: 1 | SQL: INSERT INTO "tests_author" ("name") VALUES (%s) RETURNING "tests_author"."id" | Duration: 0.0004321660000004002
Line no: 9 | Code: Post.objects.create(content=f'content {i}', author=author) | Num. Queries: 5 | SQL: INSERT INTO "tests_post" ("content", "author_id") VALUES (%s, %s) RETURNING "tests_post"."id" | Duration: 0.0008124990000002441
Line no: 13 | Code: for post in posts: | Num. Queries: 1 | SQL: SELECT "tests_post"."id", "tests_post"."content", "tests_post"."author_id" FROM "tests_post" | Duration: 4.783299999999713e-05
Line no: 14 | Code: authors.append(post.author.name) | Num. Queries: 5 | SQL: SELECT "tests_author"."id", "tests_author"."name" FROM "tests_author" WHERE "tests_author"."id" = %s LIMIT 21 | Duration: 8.804199999801199e-05
```
What can we learn from this output? Well, we can see that the line 
`authors.append(post.author.name)` was responsible for executing 5 queries. This is a quick way to identify
that we are missing a `select_related('author')` call in our `Post.objects.all()` query. This may have been obvious
in this contrived example, but in a large code base, flushing out these kinds of issues can be very useful.

Additional custom data can be added to the output as explained below in the [Reporting Options](#reporting-options) 
section.


## Limitations

We have used this on a production level code base and has out performed similar libraries in diagnosing certain kinds 
of performance issues. We however have **not** enabled it in a production environment, so proceed with caution here.
Note also that the aim of queryhunter is to identify the lines of your application code *only* which result in SQL queries.
It does not profile third party libraries (including Django itself).
Another thing to note is that this library is no where near as fancy, feature complete or as well tested as, e.g. django-silk.


### Middleware

To install the middleware, add `queryhunter.middleware.QueryHunterMiddleware` to your `MIDDLEWARE` setting:
```python
# settings.py
MIDDLEWARE = [
    # ...
    'queryhunter.middleware.QueryHunterMiddleware',
]
```
This means that all requests will be run under the `queryhunter.queryhunter` context manager. As well as
the usual query data reported by queryhunter, the middleware will also report the URL and the method of the request
which caused the queries to be executed.


### Reporting Options

TODO