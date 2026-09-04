"""Tests for Multitext's mapping surface.

`test_reader` covers what the reader builds from schema-invalid files and
`test_writer` covers what survives a save; these pin the mapping semantics
themselves — which key a repeated language resolves to, what the mutators
reach, and the two places Multitext deviates from `Mapping` on purpose.
Multitexts are built directly rather than parsed so each case states the form
list it is about.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from sil_lift import Form, Multitext, Text


def _multitext(*pairs: tuple[str | None, str]) -> Multitext:
    return Multitext(forms=[Form(lang, Text([text])) for lang, text in pairs])


def test_is_a_mapping_and_the_views_are_views() -> None:
    multitext = _multitext(("en", "dog"), ("fr", "chien"))
    assert isinstance(multitext, Mapping)
    # A view, not a list: set operations are part of what Mapping promises.
    assert multitext.keys() & {"fr", "de"} == {"fr"}
    assert multitext.keys() == {"en", "fr"}
    assert list(multitext.items()) == [("en", multitext["en"]), ("fr", multitext["fr"])]


def test_keys_are_languages_in_insertion_order() -> None:
    multitext = _multitext(("th", "a"), ("en", "b"), ("fr", "c"))
    assert list(multitext.keys()) == ["th", "en", "fr"]
    multitext["de"] = "d"
    assert list(multitext.keys()) == ["th", "en", "fr", "de"]


def test_a_repeated_language_is_one_key_answering_with_the_first_form() -> None:
    multitext = _multitext(("en", "first"), ("en", "second"), ("fr", "deux"))
    assert list(multitext.keys()) == ["en", "fr"]
    assert [str(text) for text in multitext.values()] == ["first", "deux"]
    assert str(multitext["en"]) == "first"
    assert len(multitext) == len(dict(multitext)) == 2
    # forms stays the full truth, which is where duplicate-form-lang reads from.
    assert [str(form.text) for form in multitext.forms] == ["first", "second", "deux"]


def test_a_lang_less_form_is_not_a_key() -> None:
    multitext = _multitext((None, "orphan"), ("fr", "deux"))
    assert list(multitext.keys()) == ["fr"]
    assert len(multitext) == 1
    assert None not in multitext
    # The view is a Set, so it must not claim to hold what it will not yield.
    keys = multitext.keys()
    assert None not in keys
    assert keys & {None} == set()
    assert multitext.get(None) is None  # type: ignore[call-overload]
    with pytest.raises(KeyError):
        multitext[None]  # type: ignore[index]
    assert [str(form.text) for form in multitext.forms if form.lang is None] == ["orphan"]


def test_assignment_updates_the_named_form_and_leaves_later_duplicates() -> None:
    multitext = _multitext(("en", "first"), ("en", "second"), ("fr", "deux"))
    multitext["en"] = "edited"
    # A Form carries annotations and residue the mapping cannot show a caller,
    # so assignment never discards one it was not asked about.
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


def test_deleting_through_the_mapping_while_iterating_it_reaches_every_language() -> None:
    multitext = _multitext(("en", "a"), ("fr", "b"), ("de", "c"), ("es", "d"))
    keys = multitext.keys()  # a live view, walked while its mapping shrinks
    for lang in keys:
        del multitext[lang]
    assert multitext.forms == []

    multitext = _multitext(("en", "a"), ("fr", "b"), ("de", "c"), ("es", "d"))
    for lang in multitext:
        if lang != "en":
            del multitext[lang]
    assert list(multitext.keys()) == ["en"]


def test_truthiness_asks_whether_there_is_anything_to_serialize() -> None:
    assert not Multitext()
    # Empty as a mapping, but there is a form the writer must emit. The other
    # case truthiness exists for — residue and no forms at all — needs a parsed
    # document to build, so test_writer owns it.
    lang_less = _multitext((None, "orphan"))
    assert lang_less
    assert len(lang_less) == 0


def test_equality_compares_form_lists_not_mapping_contents() -> None:
    assert _multitext(("en", "dog")) == _multitext(("en", "dog"))
    # Stricter than Mapping equality: a form no key reaches still counts.
    assert _multitext(("en", "dog")) != _multitext(("en", "dog"), (None, "orphan"))
    assert _multitext(("en", "dog")) != {"en": Text(["dog"])}


def test_repr_is_dict_shaped_until_the_forms_are_not_one_per_language() -> None:
    assert repr(Multitext()) == "Multitext({})"
    assert repr(_multitext(("en", "dog"), ("fr", "chien"))) == (
        "Multitext({'en': 'dog', 'fr': 'chien'})"
    )
    # A dict literal cannot hold either of these, and keys() excludes both, so
    # the shape changes rather than printing keys the mapping does not have.
    assert repr(_multitext(("en", "first"), ("en", "second"))) == (
        "Multitext([('en', 'first'), ('en', 'second')])"
    )
    assert repr(_multitext((None, "orphan"))) == "Multitext([(None, 'orphan')])"
    # The views repr through the mapping, so the shape reaches them too.
    assert repr(_multitext(("en", "dog")).keys()) == "KeysView(Multitext({'en': 'dog'}))"
