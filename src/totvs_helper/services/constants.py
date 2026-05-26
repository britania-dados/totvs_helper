"""Service-layer constants."""

from typing import Iterable, List

from totvs_helper.infra.odbc_client import FieldMeta

FREE_FIELDS_TO_IGNORE = {
    "char-1",
    "char-2",
    "int-1",
    "int-2",
    "dec-1",
    "dec-2",
    "log-1",
    "log-2",
    "data-1",
    "data-2",
    "check-sum",
    "cod-livre-1",
    "cod-livre-2",
    "cod-livre-3",
    "cod-livre-4",
    "cod-livre-5",
    "dat-livre-1",
    "dat-livre-2",
    "dat-livre-3",
    "dat-livre-4",
    "dat-livre-5",
    "val-livre-1",
    "val-livre-2",
    "val-livre-3",
    "val-livre-4",
    "val-livre-5",
    "log-livre-1",
    "log-livre-2",
    "log-livre-3",
    "log-livre-4",
    "log-livre-5",
    "num-livre-1",
    "num-livre-2",
    "num-livre-3",
    "num-livre-4",
    "num-livre-5",
}


def filter_fields(
    fields: Iterable[FieldMeta], include_free_fields: bool
) -> List[FieldMeta]:
    """Return fields, optionally excluding standard TOTVS free-field columns."""
    field_list = list(fields)
    if include_free_fields:
        return field_list
    return [field for field in field_list if field.name not in FREE_FIELDS_TO_IGNORE]
