import itertools

import pytest

from alma import constants
from alma.search import SearchField

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen geschaefte" role unless otherwise specified
    pytest.mark.usefixtures("generate_codes", "as_lesen_geschaefte"),
]


@pytest.mark.parametrize("lang", list(constants.Language))
def test_all_search_fields_appear_in_search_field_names(
    run_query, lang: constants.Language
):
    num_fields = len(SearchField)
    query = """
    query q($lang: Language!) { searchFieldNames(lang: $lang) { category name } }
    """
    result = run_query(query, {"lang": lang.upper()})
    assert len(result.data["searchFieldNames"]) == num_fields


@pytest.mark.parametrize("lang", list(constants.Language))
def test_search_fields_are_grouped_by_category(run_query, lang: constants.Language):
    query = """
    query q($lang: Language!) { searchFieldNames(lang: $lang) { category name } }
    """
    result = run_query(query, {"lang": lang.upper()})
    items = result.data["searchFieldNames"]

    found_categories = []
    for category, _ in itertools.groupby(items, key=lambda item: item["category"]):
        found_categories.append(category)

    assert len(found_categories) == len(set(found_categories))
