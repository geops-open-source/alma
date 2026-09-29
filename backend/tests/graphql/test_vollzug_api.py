import pytest
from sqlalchemy import select
from utils import (
    QueryError,
    make_gemeinde,
    make_vflz,
    make_vollzug,
    prefill_optional_fields,
)

from alma import constants
from alma.graphql.types import vflz as vflz_types
from alma.models import vflz as vflz_models
from alma.models.admin import InstanceSetting, SettingCategory
from alma.models.codes import BehoerdenKuerzel, CodeListe

pytestmark = [
    pytest.mark.usefixtures("generate_codes", "as_bearbeiten_sachdaten"),
]


@pytest.fixture
def bsi_behoerde_kuerzel(session):
    kuerzel_liste = session.get_one(CodeListe, constants.CodeListe.BehoerdenKuerzel)
    bsi_kuerzel_code = BehoerdenKuerzel(codeliste=kuerzel_liste, code="BSI")

    session.add(bsi_kuerzel_code)
    session.commit()
    return bsi_kuerzel_code


@pytest.fixture
def bmi_behoerde_kuerzel(session):
    kuerzel_liste = session.get_one(CodeListe, constants.CodeListe.BehoerdenKuerzel)
    bmi_kuerzel_code = BehoerdenKuerzel(codeliste=kuerzel_liste, code="BMI")

    session.add(bmi_kuerzel_code)
    session.commit()
    return bmi_kuerzel_code


def test_get_vollzug_from_vflz(session, run_query, bsi_behoerde_kuerzel):
    vflz = make_vflz(session, "My Site", 1, "combined id")
    make_vollzug(session, vflz, bsi_behoerde_kuerzel, "vollzug nummer")

    query = """
    query q($vflzId: ID!) {
        vflz(vflzId: $vflzId) {
            vollzug {
                vflnrId
                aktiv
                combinedId
                behoerde
                isDeleteable
            }
        }
    }
    """

    result = run_query(query, variable_values={"vflzId": str(vflz.vflz_id)})
    assert result.data["vflz"]["vollzug"] == [
        {
            "vflnrId": str(vflz.vollzug[0].vflnr_id),
            "aktiv": True,
            "combinedId": "combined id",
            "behoerde": "code:26030:geOps",
            "isDeleteable": False,
        },
        {
            "vflnrId": str(vflz.vollzug[1].vflnr_id),
            "aktiv": False,
            "combinedId": "vollzug nummer",
            "behoerde": "code:26030:BSI",
            "isDeleteable": True,
        },
    ]


def test_create_aktiv_vollzug_sets_behoerde_in_db(
    session, run_query, bsi_behoerde_kuerzel
):
    vflz = make_vflz(session, "My Site", 1, "vflz combined id")
    mutation = """
    mutation m($data: UpdateVflzVollzugInput!) {
        updateVflzVollzug(data: $data) {
            ... on Vflz {
                combinedId
            }
        }
    }
    """

    assert vflz.combined_id == "vflz combined id"
    run_query(
        mutation,
        variable_values={
            "data": {
                "vflzId": str(vflz.vflz_id),
                "vollzug": [
                    {
                        "vflnrId": str(vflz.vollzug[0].vflnr_id),
                        "aktiv": False,
                        "combinedId": vflz.combined_id,
                        "behoerde": str(vflz.behoerde),
                    },
                    {
                        "vflnrId": None,
                        "aktiv": True,
                        "combinedId": "this should be combined id now",
                        "behoerde": "code:26030:BSI",
                    },
                ],
            }
        },
    )

    session.refresh(vflz)
    assert vflz.combined_id == "vflz combined id"
    assert vflz.behoerde.code == "BSI"


def test_no_vollzug_active_raises(session, run_query, bsi_behoerde_kuerzel):
    vflz = make_vflz(session, "My Site")

    mutation = """
    mutation m($data: UpdateVflzVollzugInput!) {
        updateVflzVollzug(data: $data) {
            ... on ProblemGroup {
                problems {
                    message
                    problemCode
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "vflzId": str(vflz.vflz_id),
                "vollzug": [
                    {
                        "vflnrId": str(vflz.vollzug[0].vflnr_id),
                        "aktiv": False,
                        "combinedId": "this should be combined id now",
                        "behoerde": "code:26030:geOps",
                    },
                ],
            }
        },
    )
    assert result.data["updateVflzVollzug"]["problems"] == [
        {"message": "Exactly one vollzug has to be active", "problemCode": "VALIDATION"}
    ]


def test_create_teilstandort_creates_new_vollzug(
    session, run_query, bmi_behoerde_kuerzel
):
    geops_behoerde = session.scalars(
        select(BehoerdenKuerzel).where(BehoerdenKuerzel.code == "geOps")
    ).one()

    original_vflz_geom = {
        "type": "MultiPolygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [
                    [2600000, 1200010],
                    [2600010, 1200010],
                    [2600010, 1200000],
                    [2600005, 1200000],
                    [2600005, 1200005],
                    [2600000, 1200005],
                    [2600000, 1200010],
                ]
            ]
        ],
    }

    teilstandort_geometry = {
        "type": "MultiPolygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:2056"}},
        "coordinates": [
            [
                [
                    [2600000, 1200000],
                    [2600000, 1200005],
                    [2600005, 1200005],
                    [2600005, 1200000],
                    [2600000, 1200000],
                ]
            ]
        ],
    }
    gem_bern = make_gemeinde(session, "Bern", 1)
    gem_brig_glis = make_gemeinde(session, "Brig Glis", 2)

    vflz = make_vflz(session, "My Site", 1, "B:001")
    vflz.gemeinde = gem_bern
    vflz.vflgeo = vflz_models.VflGeo()
    vflz.vflgeo.set_geometry(original_vflz_geom)

    make_vollzug(session, vflz, bmi_behoerde_kuerzel, "vollzug hauptstandort nummer")

    session.commit()
    mutation = """
    mutation m($data: CreateTeilstandortInput!) {
        createTeilstandort(data: $data) {
            ... on Vflz {
                combinedId
                vollzug {
                    combinedId
                    aktiv
                    behoerde
                }
                teilstandorte {
                    combinedId
                    vollzug {
                        combinedId
                        aktiv
                        behoerde
                    }
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "parentGeometry": original_vflz_geom,
                "parentZentroid": None,
                "geometry": teilstandort_geometry,
                "zentroid": None,
                "parentVflzId": str(vflz.vflz_id),
                "gemeinde": {"hGemId": str(gem_brig_glis.h_gem_id)},
                "combinedId": "A:001.001",
                "bezeichnung": "Teilstandort von A:001",
                "flugplatz": None,
                "ktu": None,
            }
        },
    )

    assert result.data["createTeilstandort"] == {
        "combinedId": "A:001.001",
        "vollzug": [
            {"combinedId": "A:001.001", "aktiv": True, "behoerde": str(geops_behoerde)},
        ],
        "teilstandorte": [
            {
                "combinedId": "A:001.001",
                "vollzug": [
                    {
                        "combinedId": "A:001.001",
                        "aktiv": True,
                        "behoerde": str(vflz.behoerde),
                    }
                ],
            },
            {
                "combinedId": "B:001",
                "vollzug": [
                    {
                        "combinedId": "B:001",
                        "aktiv": True,
                        "behoerde": str(geops_behoerde),
                    },
                    {
                        "combinedId": "vollzug hauptstandort nummer",
                        "aktiv": False,
                        "behoerde": str(bmi_behoerde_kuerzel),
                    },
                ],
            },
        ],
    }


@pytest.mark.parametrize(
    "vollzug_editable, behoerde_vollzug, readonly",
    [
        (False, "code:26030:BMI", True),
        (True, "code:26030:BMI", False),
        (False, "code:26030:geOps", False),
        (True, "code:26030:geOps", False),
    ],
)
def test_read_only_field_graphql_vflz(
    session,
    run_query,
    bmi_behoerde_kuerzel,
    vollzug_editable,
    behoerde_vollzug,
    readonly,
):
    setting = InstanceSetting(
        key="backend.differentVollzugEditable",
        value=vollzug_editable,
        category=SettingCategory.ADMIN,
        value_schema={"type": "boolean"},
    )
    session.add(setting)

    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzVollzugInput!) {
        updateVflzVollzug(data: $data) {
            ... on Vflz {
                readOnly
            }
            ... on ProblemGroup {
                problems {
                    message
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "vflzId": str(vflz.vflz_id),
                "vollzug": [
                    {
                        "vflnrId": str(vflz.vollzug[0].vflnr_id),
                        "aktiv": behoerde_vollzug == "code:26030:geOps",
                        "combinedId": vflz.combined_id,
                        "behoerde": "code:26030:geOps",
                    },
                    {
                        "vflnrId": None,
                        "aktiv": behoerde_vollzug == "code:26030:BMI",
                        "combinedId": vflz.combined_id,
                        "behoerde": "code:26030:BMI",
                    },
                ],
            }
        },
    )

    assert result.data["updateVflzVollzug"]["readOnly"] == readonly


@pytest.mark.parametrize(
    "setting_key,setting_value,behoerde_vollzug,read_only",
    [
        ("backend.differentVollzugEditable", True, "code:26030:BMI", False),
        ("backend.differentVollzugEditable", False, "code:26030:geOps", False),
        ("backend.differentVollzugEditable", False, "code:26030:BMI", True),
        ("backend.doesNotExist", False, "code:26030:geOps", False),
    ],
)
def test_is_read_only(
    session,
    setting_key,
    setting_value,
    behoerde_vollzug,
    read_only,
    bmi_behoerde_kuerzel,
):
    behoerde_vollzug_code = BehoerdenKuerzel.from_db(session, behoerde_vollzug)
    instance_setting = InstanceSetting(
        key=setting_key,
        value=setting_value,
        category=SettingCategory.ADMIN,
        value_schema={"type": "boolean"},
    )
    session.add(instance_setting)

    vflz = make_vflz(session, "My Site")
    vflz.vollzug[0].aktiv = False

    vollzug = make_vollzug(session, vflz, behoerde_vollzug_code)
    vollzug.aktiv = True
    vflz.behoerde = behoerde_vollzug_code

    assert vflz_models.is_read_only(session, vflz) == read_only


def test_duplicate_behoerde_raises(session, run_query, bsi_behoerde_kuerzel):
    vflz = make_vflz(session, "My Site", 1, "vflz combined id")
    mutation = """
    mutation m($data: UpdateVflzVollzugInput!) {
        updateVflzVollzug(data: $data) {
            ... on ProblemGroup {
                problems {
                    message
                }
            }
        }
    }
    """

    assert vflz.combined_id == "vflz combined id"
    result = run_query(
        mutation,
        variable_values={
            "data": {
                "vflzId": str(vflz.vflz_id),
                "vollzug": [
                    {
                        "vflnrId": str(vflz.vollzug[0].vflnr_id),
                        "aktiv": False,
                        "combinedId": vflz.combined_id,
                        "behoerde": "code:26030:geOps",
                    },
                    {
                        "vflnrId": None,
                        "aktiv": True,
                        "combinedId": "this should be combined id now",
                        "behoerde": "code:26030:BSI",
                    },
                    {
                        "vflnrId": None,
                        "aktiv": False,
                        "combinedId": "this should be combined id now",
                        "behoerde": "code:26030:BSI",
                    },
                ],
            }
        },
    )
    assert result.data["updateVflzVollzug"]["problems"] == [
        {"message": "Duplicate behoerde in vollzug"}
    ]


def test_instance_behoerde_not_part_of_vollzug_raises(session, run_query):
    vflz = make_vflz(session, "My Site")
    mutation = """
    mutation m($data: UpdateVflzVollzugInput!) {
        updateVflzVollzug(data: $data) {
            ... on ProblemGroup {
                problems {
                    message
                }
            }
        }
    }
    """

    result = run_query(
        mutation,
        variable_values={
            "data": {
                "vflzId": str(vflz.vflz_id),
                "vollzug": [
                    {
                        "vflnrId": str(vflz.vollzug[0].vflnr_id),
                        "aktiv": True,
                        "combinedId": vflz.combined_id,
                        "behoerde": "code:26030:BSI",
                    },
                ],
            }
        },
    )
    assert result.data["updateVflzVollzug"]["problems"] == [
        {"message": "Instance behoerde is not part of vollzug data."}
    ]


def test_updating_read_only_vflz_raises(session, run_query, bmi_behoerde_kuerzel):
    vollzug_editable = InstanceSetting(
        key="backend.differentVollzugEditable",
        value=False,
        category=SettingCategory.ADMIN,
        value_schema={"type": "boolean"},
    )
    session.add(vollzug_editable)

    vflz = make_vflz(session, "My Site")
    vflz.vollzug[0].aktiv = False
    vollzug = make_vollzug(session, vflz, bmi_behoerde_kuerzel, "neue combined id")
    vollzug.aktiv = True
    vflz.behoerde = bmi_behoerde_kuerzel

    mutation = """
    mutation m($data: UpdateVflzDataInput!) {
        updateVflzData(data: $data) {
            ... on Vflz {
                vflzId
            }
        }
    }
    """
    variables = {
        "data": prefill_optional_fields(
            vflz_types.UpdateVflzDataInput,
            {"vflzId": str(vflz.vflz_id), "ort": "foo ort"},
        )
    }
    with pytest.raises(QueryError, match="not allowed"):
        run_query(mutation, variables)


def test_updating_vollzug_of_read_only_vflz_does_not_raise(
    session, run_query, bmi_behoerde_kuerzel
):
    """Read-only vflzs may be mutated with respect to vollzug. This is to avoid, e.g., that a
    Vollzug is (erroneously) assigned to another behoerde and you want to revoke it."""

    vollzug_editable = InstanceSetting(
        key="backend.differentVollzugEditable",
        value=False,
        category=SettingCategory.ADMIN,
        value_schema={"type": "boolean"},
    )
    session.add(vollzug_editable)

    vflz = make_vflz(session, "My Site")
    vflz.vollzug[0].aktiv = False
    vollzug = make_vollzug(session, vflz, bmi_behoerde_kuerzel, "neue combined id")
    vollzug.aktiv = True
    vflz.behoerde = bmi_behoerde_kuerzel

    mutation = """
    mutation m($data: UpdateVflzVollzugInput!) {
        updateVflzVollzug(data: $data) {
            ... on Vflz {
                vflzId
            }
        }
    }
    """
    run_query(
        mutation,
        variable_values={
            "data": {
                "vflzId": str(vflz.vflz_id),
                "vollzug": [
                    {
                        "vflnrId": str(vflz.vollzug[0].vflnr_id),
                        "aktiv": True,
                        "combinedId": vflz.combined_id,
                        "behoerde": "code:26030:geOps",
                    },
                    {
                        "vflnrId": str(vflz.vollzug[1].vflnr_id),
                        "aktiv": False,
                        "combinedId": "this should be combined id now",
                        "behoerde": "code:26030:BMI",
                    },
                ],
            }
        },
    )


def test_update_standortnummer_via_vollzug(session, run_query):
    vflz = make_vflz(session, "My Site", 1, "old_standortnummer")

    mutation = """
    mutation m($data: UpdateVflzVollzugInput!) {
        updateVflzVollzug(data: $data) {
            ... on Vflz {
                vflzId
            }
        }
    }
    """

    run_query(
        mutation,
        variable_values={
            "data": {
                "vflzId": str(vflz.vflz_id),
                "vollzug": [
                    {
                        "vflnrId": str(vflz.vollzug[0].vflnr_id),
                        "aktiv": True,
                        "combinedId": "new standortnummer",
                        "behoerde": "code:26030:geOps",
                    },
                ],
            }
        },
    )

    assert vflz.combined_id == "new standortnummer"
