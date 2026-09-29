from sqlalchemy.orm import Session
from utils import make_gemeinde


def test_query_gemeinden(session: Session, run_query, generate_codes):
    query = """
    {
        gemeinden {
            hGemId
            bfsNummer
            gemeinde
            kanton
            displayValue
        }
    }
    """
    make_gemeinde(session, "Affoltern am Albis", bfs_nummer=2)
    make_gemeinde(session, "Aeugst am Albis", bfs_nummer=3102)

    result = run_query(query)

    assert result.data == {
        "gemeinden": [
            {
                "hGemId": "2",
                "bfsNummer": 2,
                "gemeinde": "Affoltern am Albis",
                "kanton": "code:15:ZH",
                "displayValue": "Affoltern am Albis (0002)",
            },
            {
                "hGemId": "3102",
                "bfsNummer": 3102,
                "gemeinde": "Aeugst am Albis",
                "kanton": "code:15:ZH",
                "displayValue": "Aeugst am Albis (3102)",
            },
        ]
    }
