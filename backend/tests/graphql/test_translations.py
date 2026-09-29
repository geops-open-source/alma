from utils import make_translation

from alma.constants import Language


def test_german_translation(session, run_query, clear_translations):
    query = """
    {
        translations {
            de
        }
    }
    """

    translation = make_translation(session, Language.DE, "test-key")

    result = run_query(query)
    assert result.data == {"translations": {"de": {"test-key": translation.value}}}


def test_two_german_translations(session, run_query, clear_translations):
    query = """
    {
        translations {
            de
        }
    }
    """

    translation = make_translation(session, Language.DE, "test-key-1")
    translation2 = make_translation(session, Language.DE, "test-key-2")

    result = run_query(query)
    assert result.data == {
        "translations": {
            "de": {
                "test-key-1": translation.value,
                "test-key-2": translation2.value,
            }
        }
    }


def test_one_german_and_one_french_translation(session, run_query, clear_translations):
    query = """
    {
        translations {
            de
            fr
        }
    }
    """
    translation_de = make_translation(session, Language.DE, "test-key")
    translation_fr = make_translation(session, Language.FR, "test-key")

    result = run_query(query)
    assert result.data == {
        "translations": {
            "de": {"test-key": translation_de.value},
            "fr": {"test-key": translation_fr.value},
        }
    }


def test_update_translation(session, run_query, as_admin, clear_translations):
    make_translation(session, Language.DE, "test-key", "a")
    make_translation(session, Language.FR, "test-key", "b")
    make_translation(session, Language.IT, "test-key", "c")

    mutation = """
    mutation m($data: UpdateTranslationInput!) {
        updateTranslation(data: $data)
    }
    """

    result = run_query(
        mutation,
        {
            "data": {
                "key": "test-key",
                "translation": {"de": "de value", "fr": "fr value", "it": "it value"},
            }
        },
    )
    assert result.data["updateTranslation"] == "test-key"

    translations_result = run_query("{ translations { de fr it } }")
    assert translations_result.data == {
        "translations": {
            "de": {"test-key": "de value"},
            "fr": {"test-key": "fr value"},
            "it": {"test-key": "it value"},
        }
    }
