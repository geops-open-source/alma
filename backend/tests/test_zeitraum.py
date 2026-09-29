from datetime import date

import pytest

from alma.protocols import ZeitraumData, merge


@pytest.mark.parametrize(
    "objs, result",
    [
        (
            [
                ZeitraumData(),
                ZeitraumData(zeitraum_vonjahr=False, zeitraum_bisheute=True),
                ZeitraumData(zeitraum_vonjahr=True, zeitraum_bisheute=False),
            ],
            ZeitraumData(zeitraum_vonjahr=False, zeitraum_bisheute=True),
        ),
        (
            [
                ZeitraumData(zeitraum_von=date(2020, 1, 1)),
                ZeitraumData(zeitraum_von=date(2019, 2, 3)),
                ZeitraumData(zeitraum_von=date(2018, 2, 3)),
            ],
            ZeitraumData(zeitraum_von=date(2018, 2, 3)),
        ),
        (
            [
                ZeitraumData(
                    zeitraum_von=date(2020, 1, 1), zeitraum_bis=date(2023, 3, 6)
                ),
                ZeitraumData(
                    zeitraum_von=date(2019, 3, 4),
                    zeitraum_vonjahr=True,
                    zeitraum_bis=date(2022, 3, 4),
                ),
            ],
            ZeitraumData(
                zeitraum_von=date(2019, 3, 4),
                zeitraum_vonjahr=True,
                zeitraum_bis=date(2023, 3, 6),
            ),
        ),
        (
            [
                ZeitraumData(),
                ZeitraumData(
                    zeitraum_von=date(2019, 1, 1), zeitraum_bis=date(2022, 3, 1)
                ),
                ZeitraumData(
                    zeitraum_von=date(2018, 1, 1), zeitraum_bis=date(2023, 3, 1)
                ),
                ZeitraumData(
                    zeitraum_von=date(2020, 1, 1), zeitraum_bis=date(2024, 3, 1)
                ),
                ZeitraumData(
                    zeitraum_von=date(2019, 3, 1),
                    zeitraum_vonjahr=True,
                    zeitraum_bis=date(2026, 3, 1),
                    zeitraum_bisjahr=True,
                ),
                ZeitraumData(
                    zeitraum_von=date(2020, 2, 1),
                    zeitraum_bis=date(2027, 3, 1),
                    zeitraum_bisjahr=True,
                ),
            ],
            ZeitraumData(
                zeitraum_von=date(2018, 1, 1),
                zeitraum_bis=date(2027, 3, 1),
                zeitraum_bisjahr=True,
            ),
        ),
        (
            [
                ZeitraumData(zeitraum_vonjahr=True),
                ZeitraumData(zeitraum_von=date(2022, 1, 1)),
            ],
            ZeitraumData(zeitraum_von=date(2022, 1, 1)),
        ),
        ([], ZeitraumData()),
    ],
)
def test_merge(objs, result):
    assert merge(objs) == result
