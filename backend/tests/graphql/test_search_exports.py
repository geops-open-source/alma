import pytest
from sqlalchemy.orm import Session
from utils import make_saved_search, make_search_export

from alma.models.auth import User

pytestmark = [
    # Fixture required by all tests in this module
    # Run all tests in this module using the "lesen sachdaten" role unless otherwise specified
    pytest.mark.usefixtures("as_lesen_sachdaten"),
]


def test_query_returns_exports_of_current_user(session: Session, run_query, context):
    other_user = User(username="other-user", email="other@example.com", sub="sub-foo")
    session.add(other_user)

    search1 = make_saved_search(
        session,
        name="export0001",
        is_temporary=True,
        user=context.user,
        query=[
            {
                "__type__": "expression",
                "name": "bezeichnung",
                "operator": "~",
                "value": "test",
            }
        ],
    )
    search_export1 = make_search_export(session, search1)
    session.add(search_export1)

    search2 = make_saved_search(
        session,
        name="export0002",
        is_temporary=True,
        user=other_user,
        query=[
            {
                "__type__": "expression",
                "name": "bezeichnung",
                "operator": "~",
                "value": "test",
            }
        ],
    )
    search_export2 = make_search_export(session, search2)
    session.add(search_export2)

    query = """
    query q($exportId: ID) {
        searchExports(exportId: $exportId) {
            exportId
        }
    }
    """

    result = run_query(query, variable_values={"exportId": None})
    assert result.data["searchExports"] == [{"exportId": "export0001"}]

    result = run_query(query, variable_values={"exportId": "export0001"})
    assert result.data["searchExports"] == [{"exportId": "export0001"}]

    result = run_query(query, variable_values={"exportId": "export0002"})
    assert result.data["searchExports"] == []
