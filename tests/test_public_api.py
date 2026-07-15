"""B7 discipline: no lxml type may appear anywhere in the public surface."""

import inspect
import typing

import sil_lift


def _hint_names(obj: object) -> list[str]:
    try:
        hints = typing.get_type_hints(obj)
    except Exception:
        return []
    return [repr(hint) for hint in hints.values()]


def test_no_lxml_in_public_annotations() -> None:
    offenders: list[str] = []
    for name in sil_lift.__all__:
        public = getattr(sil_lift, name)
        for hint in _hint_names(public):
            if "lxml" in hint:
                offenders.append(f"{name}: {hint}")
        if inspect.isclass(public):
            for member_name, member in inspect.getmembers(public):
                if member_name.startswith("_") and member_name not in ("__init__",):
                    continue
                if inspect.isfunction(member):
                    for hint in _hint_names(member):
                        if "lxml" in hint:
                            offenders.append(f"{name}.{member_name}: {hint}")
    assert not offenders, f"lxml types leaked into the public API: {offenders}"


def test_all_names_exist_and_sorted() -> None:
    for name in sil_lift.__all__:
        assert hasattr(sil_lift, name)
    assert sil_lift.__all__ == sorted(sil_lift.__all__)
