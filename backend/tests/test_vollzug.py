import pytest
from utils import make_vflz, make_vollzug

from alma import constants
from alma.models.admin import InstanceSetting, SettingCategory
from alma.models.codes import BehoerdenKuerzel, CodeListe
from alma.settings import settings

pytestmark = [
    pytest.mark.usefixtures("generate_codes", "as_bearbeiten_sachdaten"),
]


@pytest.fixture
def bmi_behoerde_kuerzel(session):
    kuerzel_liste = session.get_one(CodeListe, constants.CodeListe.BehoerdenKuerzel)
    bmi_kuerzel_code = BehoerdenKuerzel(codeliste=kuerzel_liste, code="BMI")

    session.add(bmi_kuerzel_code)
    session.commit()
    return bmi_kuerzel_code


def test_setting_vflz_combined_id_to_vollzug_of_non_instance_behoerde_raises(
    session, bmi_behoerde_kuerzel, test_settings
):
    settings.behoerde = "geOps"

    vollzug_editable = InstanceSetting(
        key="backend.differentVollzugEditable",
        value=False,
        category=SettingCategory.ADMIN,
        value_schema={"type": "boolean"},
    )
    session.add(vollzug_editable)

    vflz = make_vflz(session, "My Site")
    vflz.vollzug[0].aktiv = False
    vollzug = make_vollzug(session, vflz, bmi_behoerde_kuerzel)
    vollzug.aktiv = True
    vflz.behoerde = bmi_behoerde_kuerzel

    with pytest.raises(
        AttributeError,
        match="Combined_id to be set is not equal to vollzug of instance setting.",
    ):
        vflz.combined_id = vflz.vollzug[1].combined_id


def test_setting_vflz_behoerde_to_non_active_vollzug_raises(
    session, bmi_behoerde_kuerzel, test_settings
):
    settings.behoerde = "geOps"

    vollzug_editable = InstanceSetting(
        key="backend.differentVollzugEditable",
        value=False,
        category=SettingCategory.ADMIN,
        value_schema={"type": "boolean"},
    )
    session.add(vollzug_editable)

    vflz = make_vflz(session, "My Site")
    vflz.vollzug[0].aktiv = False
    vollzug = make_vollzug(session, vflz, bmi_behoerde_kuerzel)
    vollzug.aktiv = True

    with pytest.raises(
        AttributeError, match="Behoerde to be set is not equal to active vollzug."
    ):
        vflz.behoerde = vflz.vollzug[0].behoerde
