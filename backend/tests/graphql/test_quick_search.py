import pytest
from utils import make_gemeinde, make_vflz

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_lesen_sachdaten"),
]


def test_quick_search_results(session, run_query):
    site_a1 = make_vflz(session, "Standort A-1", vfl_id=1, combined_id="combined-id-1")
    site_a2 = make_vflz(session, "Standort A-2", vfl_id=2, combined_id="combined-id-2")
    make_vflz(session, "Standort B-1", vfl_id=3)

    query = """
    query q($query: String!) {
        search(query: $query) {
            graph { results { vflzId combinedId } }
        }
    }
    """

    response = run_query(query, {"query": "Standort A"})
    assert response.data["search"]["graph"]["results"] == [
        {"vflzId": str(site_a1.vflz_id), "combinedId": "combined-id-1"},
        {"vflzId": str(site_a2.vflz_id), "combinedId": "combined-id-2"},
    ]


def test_quick_search_results_can_be_paginated(session, run_query):
    site_a1 = make_vflz(session, "Standort A-1", vfl_id=1, combined_id="A999")
    site_a2 = make_vflz(session, "Standort A-2", vfl_id=2, combined_id="A111")
    site_a3 = make_vflz(session, "Standort A-3", vfl_id=3, combined_id="A222")

    query = """
    query q($query: String!, $page: Int!, $perPage: Int!) {
        search(query: $query, page: $page, perPage: $perPage) {
            graph {
                numPages
                numResultsTotal
                results { vflzId combinedId }
            }
        }
    }
    """

    response = run_query(query, {"query": "Standort", "perPage": 2, "page": 1})
    result = response.data["search"]["graph"]

    assert result["results"] == [
        {"vflzId": str(site_a2.vflz_id), "combinedId": "A111"},
        {"vflzId": str(site_a3.vflz_id), "combinedId": "A222"},
    ]
    assert result["numPages"] == 2
    assert result["numResultsTotal"] == 3

    response = run_query(query, {"query": "Standort", "perPage": 2, "page": 2})
    result = response.data["search"]["graph"]

    assert result["results"] == [
        {"vflzId": str(site_a1.vflz_id), "combinedId": "A999"},
    ]
    assert result["numPages"] == 2
    assert result["numResultsTotal"] == 3


def test_quick_search_results_are_sorted_by_combined_id(session, run_query):
    site_a1 = make_vflz(session, "Standort A-1", vfl_id=1, combined_id="A999")
    site_a2 = make_vflz(session, "Standort A-2", vfl_id=2, combined_id="A111")
    site_a3 = make_vflz(session, "Standort A-3", vfl_id=3, combined_id="A222")

    query = """
    query q($query: String!) {
        search(query: $query) {
            graph {
                results { vflzId combinedId }
            }
        }
    }
    """

    response = run_query(query, {"query": "Standort A"})
    assert response.data["search"]["graph"]["results"] == [
        {"vflzId": str(site_a2.vflz_id), "combinedId": "A111"},
        {"vflzId": str(site_a3.vflz_id), "combinedId": "A222"},
        {"vflzId": str(site_a1.vflz_id), "combinedId": "A999"},
    ]


def test_quick_search_results_are_sorted_by_combined_id_and_bezeichnung_alphabetically(
    session, run_query
):
    site_a1 = make_vflz(session, "A111a", vfl_id=1, combined_id="A999a")
    site_a2 = make_vflz(session, "Standort A-2", vfl_id=2, combined_id="A111a")
    site_a3 = make_vflz(session, "Standort A-3", vfl_id=3, combined_id="A222a")
    site_a3.strasse = "A111a Straße"

    query = """
    query q($query: String!) {
        search(query: $query) {
            graph {
                results { vflzId }
            }
        }
    }
    """

    response = run_query(query, {"query": "A111"})
    assert response.data["search"]["graph"]["results"] == [
        {"vflzId": str(site_a2.vflz_id)},
        {"vflzId": str(site_a1.vflz_id)},
        {"vflzId": str(site_a3.vflz_id)},
    ]


def test_quick_search_results_prioritize_combined_id_and_bezeichnung_matches_over_non_matches(
    session, run_query
):
    site_a1 = make_vflz(session, "Standort A-1", vfl_id=1, combined_id="A999a")
    site_a2 = make_vflz(session, "Standort A-2", vfl_id=2, combined_id="A111a")
    site_a3 = make_vflz(session, "A111a", vfl_id=3, combined_id="A222a")
    site_a1.strasse = "A111 Straße"

    query = """
    query q($query: String!) {
        search(query: $query) {
            graph {
                results { vflzId }
            }
        }
    }
    """

    response = run_query(query, {"query": "A111"})
    assert response.data["search"]["graph"]["results"] == [
        {"vflzId": str(site_a2.vflz_id)},
        {"vflzId": str(site_a3.vflz_id)},
        {"vflzId": str(site_a1.vflz_id)},
    ]


def test_quick_search_with_valid_filters_filters_out_found_vflz_ids(session, run_query):
    gem = make_gemeinde(session, name="Foo Gemeinde", bfs_nummer=4)

    site_a1 = make_vflz(session, "Standort A-1", vfl_id=1, combined_id="A999a")
    site_a1.gemeinde = gem
    site_a2 = make_vflz(session, "Standort A", vfl_id=2, combined_id="A111a")
    site_a2.gemeinde = gem
    site_a3 = make_vflz(session, "Standort A-3", vfl_id=3, combined_id="A222a")
    site_a3.gemeinde = gem

    query = """
        query q($query: String!, $filters: [SearchFilter!]) {
            search(
                advanced: false
                query: $query
                filters: $filters
                fields: [ BEZEICHNUNG ]
            ) {
                tabular {
                    numResultsTotal
                }
            }
        }
    """

    response = run_query(
        query, {"query": "Standort A", "filters": [{"field": "BFS_NR", "value": [3]}]}
    )
    assert response.data["search"]["tabular"]["numResultsTotal"] == 0

    response = run_query(
        query, {"query": "Standort A", "filters": [{"field": "BFS_NR", "value": [4]}]}
    )
    assert response.data["search"]["tabular"]["numResultsTotal"] > 0
