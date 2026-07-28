import inspect

import sil_lift


def _annotation_strings(obj: object) -> list[str]:
    """Raw source annotations for a function or class.

    Static (PEP 563 strings) rather than resolved: ``typing.get_type_hints``
    raises on the TYPE_CHECKING-only imports several public signatures use
    (``os``, ``Iterator``, ...), and silently skipping those members — as an
    earlier ``try/except: return []`` did — let the check pass without ever
    examining them. lxml only ever enters this codebase as ``from lxml import
    etree``, so a leak is always visible in the source text as an ``etree.``
    (or ``lxml``) reference; no resolution is needed to catch it.
    """
    return [str(hint) for hint in getattr(obj, "__annotations__", {}).values()]


def _leaks_lxml(annotation: str) -> bool:
    return "lxml" in annotation or "etree." in annotation


def test_no_lxml_in_public_annotations() -> None:
    offenders: list[str] = []
    for name in sil_lift.__all__:
        public = getattr(sil_lift, name)
        offenders += [f"{name}: {a}" for a in _annotation_strings(public) if _leaks_lxml(a)]
        if inspect.isclass(public):
            for member_name, member in inspect.getmembers(public):
                if member_name.startswith("_") and member_name != "__init__":
                    continue
                if inspect.isfunction(member):
                    offenders += [
                        f"{name}.{member_name}: {a}"
                        for a in _annotation_strings(member)
                        if _leaks_lxml(a)
                    ]
    assert not offenders, f"lxml types leaked into the public API: {offenders}"


def test_all_names_exist_and_sorted() -> None:
    for name in sil_lift.__all__:
        assert hasattr(sil_lift, name)
    assert sil_lift.__all__ == sorted(sil_lift.__all__)
