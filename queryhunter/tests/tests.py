from django.test import Client
import pytest
from django.urls import reverse

from queryhunter import query_hunter
from queryhunter.reporting import QueryHunterPrintingOptions
from queryhunter.tests.my_module import get_authors, create_posts


@pytest.mark.django_db(transaction=True)
def test_queryhunter():
    create_posts()
    with query_hunter(func='get_authors', username='Paul') as qh:
        get_authors()
    query_info = qh.query_info
    assert len(query_info) == 1
    file_data = query_info['django-queryhunter/queryhunter/tests/my_module.py']
    assert len(file_data.lines) == 2

    first_line = file_data.lines[0]
    assert first_line.line_no == 13
    assert first_line.count == 1
    assert first_line.duration > 0
    assert first_line.sql == (
        'SELECT "tests_post"."id", "tests_post"."content", "tests_post"."author_id" FROM "tests_post"'
    )
    assert first_line.code == 'for post in posts:'
    assert first_line.meta_data == {'func': 'get_authors', 'username': 'Paul'}

    second_line = file_data.lines[1]
    assert second_line.line_no == 14
    assert second_line.count == 5
    assert second_line.duration > 0
    assert second_line.code == 'authors.append(post.author.name)'


@pytest.mark.django_db(transaction=True)
def test_queryhunter_modules_reporting_options():
    create_posts()
    options = QueryHunterPrintingOptions(
        modules=[
            'django-queryhunter/queryhunter/tests/my_module.py',
            'django-queryhunter/queryhunter/tests/not_my_module.py',
        ],
    )
    with query_hunter(reporting_options=options) as qh:
        get_authors()
    query_info = qh.query_info
    assert len(query_info) == 1

    options = QueryHunterPrintingOptions(modules=['django-queryhunter/queryhunter/tests/not_my_module.py'])
    with query_hunter(reporting_options=options) as qh:
        get_authors()
    query_info = qh.query_info
    assert len(query_info) == 0

    options = QueryHunterPrintingOptions(max_sql_length=5)
    with query_hunter(reporting_options=options) as qh:
        get_authors()
    query_info = qh.query_info
    file_data = query_info['django-queryhunter/queryhunter/tests/my_module.py']
    first_line = file_data.lines[0]
    assert len(first_line.sql) == 5

    options = QueryHunterPrintingOptions(sort_by='-count')
    with query_hunter(reporting_options=options) as qh:
        get_authors()
    query_info = qh.query_info
    file_data = query_info['django-queryhunter/queryhunter/tests/my_module.py']
    first_line = file_data.lines[0]
    assert first_line.count == 5
    second_line = file_data.lines[1]
    assert second_line.count == 1

    options = QueryHunterPrintingOptions(sort_by='count')
    with query_hunter(reporting_options=options) as qh:
        get_authors()
    query_info = qh.query_info
    file_data = query_info['django-queryhunter/queryhunter/tests/my_module.py']
    first_line = file_data.lines[0]
    assert first_line.count == 1
    second_line = file_data.lines[1]
    assert second_line.count == 5


@pytest.mark.django_db(transaction=True)
def test_queryhunter_middleware():
    create_posts()
    client = Client()
    response = client.get(reverse('authors'))
    assert response.status_code == 200
