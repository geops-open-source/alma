from alma.settings import FieldMapping, WfsSettings, settings
from alma.wfs_cache import update_custom_code_mapping


def test_validation_gws_custom_code_mappings(wfs_test_settings):
    settings.wfs_config["gws_bereich"] = WfsSettings(
        is_proxy=False,
        is_cache=True,
        url="",
        layers=["ms:gewaesserschutzbereich_ao", "ms:zustroembereich_zu"],
        field_mappings=[
            FieldMapping(
                wfs="typ",
                cache_table="gws_bereich",
                code_mappings={"Au": "AuZu", "Zu": "AuZu"},
            )
        ],
    )
    wfs_results = [
        {"gws_bereich": "Au", "wkb_geometry": "geom-1"},
        {"gws_bereich": "Zu", "wkb_geometry": "geom-2"},
        {"gws_bereich": "Sonstige", "wkb_geometry": "geom-3"},
    ]

    update_custom_code_mapping(settings.wfs_config["gws_bereich"], wfs_results)

    assert wfs_results == [
        {"gws_bereich": "AuZu", "wkb_geometry": "geom-1"},
        {"gws_bereich": "AuZu", "wkb_geometry": "geom-2"},
        {"gws_bereich": "Sonstige", "wkb_geometry": "geom-3"},
    ]
