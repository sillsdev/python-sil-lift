"""Tests for Multitext's key-access surface.

`test_reader` covers what the reader builds from schema-invalid files and
`test_writer` covers what survives a save; these pin the semantics themselves.
Multitexts are built directly rather than parsed so each case states the form
list it is about.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from sil_lift import Form, Multitext, Text


def _multitext(*pairs: tuple[str | None, str]) -> Multitext:
    return Multitext(forms=[Form(lang, Text([text])) for lang, text in pairs])


def test_is_not_a_mapping_and_the_accessors_return_lists() -> None:
    multitext = _multitext(("en", "dog"), ("fr", "chien"))
    # Deliberate: nothing here claims a contract it does not implement.
    assert not isinstance(multitext, Mapping)
    assert multitext.keys() == ["en", "fr"]
    assert multitext.items() == [("en", multitext["en"]), ("fr", multitext["fr"])]
    assert {lang: str(text) for lang, text in dict(multitext).items()} == {
        "en": "dog",
        "fr": "chien",
    }


def test_keys_are_languages_in_insertion_order() -> None:
    multitext = _multitext(("th", "a"), ("en", "b"), ("fr", "c"))
    assert multitext.keys() == ["th", "en", "fr"]
    multitext["de"] = "d"
    assert multitext.keys() == ["th", "en", "fr", "de"]


def test_a_repeated_language_is_one_key_answering_with_the_first_form() -> None:
    multitext = _multitext(("en", "first"), ("en", "second"), ("fr", "deux"))
    assert multitext.keys() == ["en", "fr"]
    # keys(), values() and items() stay parallel, so zip and dict agree.
    assert [str(text) for text in multitext.values()] == ["first", "deux"]
    assert str(multitext["en"]) == "first"
    assert len(multitext.keys()) == len(multitext.values()) == len(dict(multitext)) == 2
    # forms stays the full truth, which is where duplicate-form-lang reads from.
    assert [str(form.text) for form in multitext.forms] == ["first", "second", "deux"]


def test_a_lang_less_form_is_not_a_key() -> None:
    multitext = _multitext((None, "orphan"), ("fr", "deux"))
    assert multitext.keys() == ["fr"]
    assert None not in multitext
    assert multitext.get(None) is None  # type: ignore[arg-type]
    with pytest.raises(KeyError):
        multitext[None]  # type: ignore[index]
    assert [str(form.text) for form in multitext.forms if form.lang is None] == ["orphan"]


def test_there_is_no_len_so_a_caller_says_which_count_they_mean() -> None:
    multitext = _multitext((None, "orphan"), ("en", "first"), ("en", "second"))
    with pytest.raises(TypeError):
        len(multitext)  # type: ignore[arg-type]
    assert len(multitext.keys()) == 1
    assert len(multitext.forms) == 3


def test_assignment_updates_the_named_form_and_leaves_later_duplicates() -> None:
    multitext = _multitext(("en", "first"), ("en", "second"), ("fr", "deux"))
    multitext["en"] = "edited"
    # A Form carries annotations and residue no key reaches, so assignment
    # never discards one it was not asked about.
    assert [(form.lang, str(form.text)) for form in multitext.forms] == [
        ("en", "edited"),
        ("en", "second"),
        ("fr", "deux"),
    ]


def test_assignment_coerces_a_plain_string_and_appends_a_new_language() -> None:
    multitext = Multitext()
    multitext["en"] = "dog"
    assert isinstance(multitext["en"], Text)
    assert str(multitext["en"]) == "dog"
    text = Text(["chien"])
    multitext["fr"] = text
    assert multitext["fr"] is text


def test_deletion_removes_every_form_for_the_language() -> None:
    multitext = _multitext(("en", "first"), ("en", "second"), (None, "orphan"), ("fr", "deux"))
    del multitext["en"]
    assert "en" not in multitext
    assert [(form.lang, str(form.text)) for form in multitext.forms] == [
        (None, "orphan"),
        ("fr", "deux"),
    ]
    with pytest.raises(KeyError):
        del multitext["en"]


def test_deleting_while_iterating_reaches_every_language() -> None:
    multitext = _multitext(("en", "a"), ("fr", "b"), ("de", "c"), ("es", "d"))
    for lang in multitext:
        del multitext[lang]
    assert multitext.forms == []

    multitext = _multitext(("en", "a"), ("fr", "b"), ("de", "c"), ("es", "d"))
    for lang in multitext:
        if lang != "en":
            del multitext[lang]
    assert multitext.keys() == ["en"]


def test_truthiness_asks_whether_there_is_anything_to_serialize() -> None:
    assert not Multitext()
    # No keys, but there is a form the writer must emit. The other case
    # truthiness exists for — residue and no forms at all — needs a parsed
    # document to build, so test_writer owns it.
    lang_less = _multitext((None, "orphan"))
    assert lang_less
    assert lang_less.keys() == []


def test_equality_compares_form_lists() -> None:
    assert _multitext(("en", "dog")) == _multitext(("en", "dog"))
    # A form no key reaches still counts.
    assert _multitext(("en", "dog")) != _multitext(("en", "dog"), (None, "orphan"))


def test_repr_is_always_a_list_of_pairs() -> None:
    assert repr(Multitext()) == "Multitext([])"
    assert repr(_multitext(("en", "dog"), ("fr", "chien"))) == (
        "Multitext([('en', 'dog'), ('fr', 'chien')])"
    )
    # One shape whatever forms holds, so it can never print a dict literal
    # that cannot exist and whose keys contradict keys().
    assert repr(_multitext(("en", "first"), ("en", "second"))) == (
        "Multitext([('en', 'first'), ('en', 'second')])"
    )
    assert repr(_multitext((None, "orphan"))) == "Multitext([(None, 'orphan')])"
