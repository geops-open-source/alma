def test_validate_search_query(run_query):
    query = """
    query q($query: String!) {
        validateSearchQuery(query: $query) {
            message problemCode field messageCode messageArgs
        }
    }
    """

    response = run_query(query, {"query": "A = 1"})
    assert response.data["validateSearchQuery"] == {
        "message": "Unknown field name: A",
        "problemCode": "VALIDATION",
        "field": "query",
        "messageCode": "search.validation.unknownField",
        "messageArgs": {"context": "A"},
    }

    response = run_query(query, {"query": "ZZZ = 1"})
    assert response.data["validateSearchQuery"] == {
        "message": "Unknown field name: ZZZ",
        "problemCode": "VALIDATION",
        "field": "query",
        "messageCode": "search.validation.unknownField",
        "messageArgs": {"context": "ZZZ"},
    }

    response = run_query(query, {"query": "A = "})
    assert response.data["validateSearchQuery"] == {
        "message": "Syntax error: Incomplete expression",
        "problemCode": "VALIDATION",
        "field": "query",
        "messageCode": "search.validation.incompleteExpression",
        "messageArgs": {},
    }

    response = run_query(query, {"query": "A = $foo"})
    assert response.data["validateSearchQuery"] == {
        "message": "Invalid token: '$foo'",
        "problemCode": "VALIDATION",
        "field": "query",
        "messageCode": "search.validation.invalidToken",
        "messageArgs": {"context": "$foo"},
    }

    response = run_query(query, {"query": 'Bezeichnung ~ "foo"'})
    assert response.data["validateSearchQuery"] is None
