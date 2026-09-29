from collections.abc import Iterator
from typing import Any, cast

import pytest

from alma.tools import pull_gemeinden


class FakeGeometry:
    def ExportToWkb(self) -> bytes:
        return b"geom"


class FakeCursor:
    def __init__(self) -> None:
        self.statements: list[tuple[str, Any]] = []
        self.rowcount = 1
        self.fetchone_result: tuple[int] | None = (2,)

    def execute(self, statement: str, params: Any = None) -> None:
        self.statements.append((statement, params))
        self.rowcount = 1

    def fetchone(self) -> tuple[int] | None:
        return self.fetchone_result

    def close(self) -> None:
        pass


class FakeConnection:
    def __init__(self) -> None:
        self.cursors: list[FakeCursor] = []
        self.commits = 0

    @property
    def statements(self) -> list[tuple[str, Any]]:
        return [statement for cursor in self.cursors for statement in cursor.statements]

    def cursor(self) -> FakeCursor:
        cursor = FakeCursor()
        self.cursors.append(cursor)
        return cursor

    def commit(self) -> None:
        self.commits += 1


def test_settings_kantone_used(monkeypatch):
    # Simulate settings.gemeinde_service.kantone
    monkeypatch.setattr(
        pull_gemeinden.settings.gemeinde_service, "kantone", ["BE", "VD"]
    )
    called = {}

    def fake_import_gemeinden(conn, kantone=None):
        called["kantone"] = kantone

    def fake_import_orte(conn, kantone=None):
        called["orte_kantone"] = kantone

    monkeypatch.setattr(pull_gemeinden, "import_gemeinden", fake_import_gemeinden)
    monkeypatch.setattr(pull_gemeinden, "import_orte", fake_import_orte)
    pull_gemeinden.main()
    assert called["kantone"] == ["BE", "VD"]
    assert called["orte_kantone"] == ["BE", "VD"]


def test_import_gemeinden_uses_only_matching_kantone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bern = {
        "bfs_nummer": "351",
        "name": "Bern",
        "kanton_nummer": "2",
        "_geom_": FakeGeometry(),
        "_srid_": 2056,
    }
    zurich = {
        "bfs_nummer": "261",
        "name": "Zuerich",
        "kanton_nummer": "1",
        "_geom_": FakeGeometry(),
        "_srid_": 2056,
    }

    def fake_feature_iterator(*_args: object) -> Iterator[dict[str, Any]]:
        yield bern
        yield zurich

    monkeypatch.setattr(pull_gemeinden, "feature_iterator", fake_feature_iterator)
    conn = FakeConnection()

    # Simulate get_kanton_nummern returning ["2", "3"] for kantone ["BE", "VD"]
    monkeypatch.setattr(
        pull_gemeinden, "get_kanton_nummern", lambda db, kantone: ["2", "3"]
    )

    pull_gemeinden.import_gemeinden(cast(Any, conn), kantone=["BE", "VD"])
    statements = conn.statements
    assert statements[0] == ("delete from alma.h_gem", None)
    assert any(params is bern for _, params in statements)
    assert not any(params is zurich for _, params in statements)

    delete_statements = [
        (statement, params)
        for statement, params in statements
        if statement.startswith("delete from alma.h_gem")
    ]
    assert delete_statements == [("delete from alma.h_gem", None)]
    assert conn.commits == 1


def test_import_orte_filters_by_intersection_with_kantone_gemeinden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ort = {
        "plz": "3000",
        "name": "Bern",
        "_geom_": FakeGeometry(),
        "_srid_": 2056,
    }

    def fake_feature_iterator(*_args: object) -> Iterator[dict[str, Any]]:
        yield ort

    monkeypatch.setattr(pull_gemeinden, "feature_iterator", fake_feature_iterator)
    conn = FakeConnection()

    pull_gemeinden.import_orte(cast(Any, conn), kantone=["BE", "VD"])

    statements = conn.statements
    delete_statement, delete_params = statements[0]
    assert delete_statement.startswith("delete from alma.h_ort ort")
    assert "ST_Intersects" in delete_statement
    assert delete_params == (["BE", "VD"],)

    insert_statements = [
        (statement, params)
        for statement, params in statements
        if statement.startswith("insert into alma.h_ort")
    ]
    assert len(insert_statements) == 1
    insert_statement, insert_params = insert_statements[0]
    assert "ST_Intersects" in insert_statement
    assert insert_params[-1] == ["BE", "VD"]
    assert conn.commits == 1
