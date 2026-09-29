def test_search_autosuggest(run_query):
    query = """
    query q($input: String!, $pos: Int!, $lang: Language!) {
        autosuggestSearchQuery(input: $input, pos: $pos, lang: $lang) {
            type value category, fieldType
        }
    }
    """

    response = run_query(query, {"input": "Beurt", "pos": 5, "lang": "DE"})
    assert response.data["autosuggestSearchQuery"] == [
        {
            "type": "FIELD_NAME",
            "value": "Beurteilung",
            "category": "BEURTEILUNG",
            "fieldType": None,
        }
    ]

    response = run_query(query, {"input": "Beurtzzzzz", "pos": 5, "lang": "DE"})
    assert response.data["autosuggestSearchQuery"] == [
        {
            "type": "FIELD_NAME",
            "value": "Beurteilung",
            "category": "BEURTEILUNG",
            "fieldType": None,
        }
    ]

    response = run_query(query, {"input": "Beurtzzzzz", "pos": 6, "lang": "DE"})
    assert response.data["autosuggestSearchQuery"] == []

    response = run_query(query, {"input": "Beurteilung ", "pos": 12, "lang": "DE"})
    assert response.data["autosuggestSearchQuery"] == [
        {
            "type": "OPERATOR",
            "value": "=",
            "category": None,
            "fieldType": "CODE",
        },
        {
            "type": "OPERATOR",
            "value": "!=",
            "category": None,
            "fieldType": "CODE",
        },
    ]
