from __future__ import annotations

from apps.common.pagination import StandardCursorPagination


def test_standard_cursor_pagination_defaults() -> None:
    paginator = StandardCursorPagination()

    assert paginator.page_size == 20
    assert paginator.max_page_size == 100
    assert paginator.ordering == "-created_at"
    assert paginator.page_size_query_param == "page_size"
