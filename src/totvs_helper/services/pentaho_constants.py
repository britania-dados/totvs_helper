"""Constants for Pentaho PDI load generation and DSN defaults."""

from __future__ import annotations

from typing import List, Tuple

DEFAULT_INCLUDE_FREE_FIELDS = True

# Families that use five sources (EMPRESA) in one transformation.
MULTI_SOURCE_FAMILIES = frozenset({"esp2unit", "ems2unit", "mov2unit"})

# Multi-empresa: five establishments in one transformation.
MULTI_BRANCHES: List[Tuple[str, str]] = [
    ("BRIC", "35"),
    ("ECOM", "E1"),
    ("ELETRO", "1"),
    ("NORDESTE", "15"),
    ("PHILCO", "30"),
]

# Non-multi: two logical bases in one tot.* table.
NON_MULTI_BASES: List[Tuple[str, str, str]] = [
    # (step_name, connection_name, base_literal)
    ("WMS", "WMS", "VAREJO"),
    ("WMS_ECOM", "WMS_ECOM", "ECOM"),
]

NON_MULTI_BASES_ESP2CORP: List[Tuple[str, str, str]] = [
    ("VAREJO", "DATASUL_ESP2CORP", "VAREJO"),
    ("ECOM", "DATASUL_ESP2CORP_ECOM", "ECOM"),
]

SOURCE_FAMILIES = ("esp2unit", "ems2unit", "mov2unit", "esp2corp", "wms")

MULTI_TEMPLATE_BY_FAMILY = {
    "esp2unit": "multi_esp2unit",
    "ems2unit": "multi_ems2unit",
    "mov2unit": "multi_ems2unit",
}

CONNECTION_PREFIX_BY_FAMILY = {
    "esp2unit": "DATASUL_ESP2UNIT",
    "ems2unit": "DATASUL_EMS2UNIT",
    "mov2unit": "DATASUL_MOV2UNIT",
}

NON_MULTI_TEMPLATE_BY_FAMILY = {
    "wms": "non_multi_wms",
    "esp2corp": "non_multi_esp2corp",
}


def detect_source_family(dsn: str) -> str:
    """Infer OpenEdge family from ODBC DSN name."""
    upper = (dsn or "").upper()
    for family in ("ESP2UNIT", "EMS2UNIT", "MOV2UNIT", "ESP2CORP", "WMS"):
        if family in upper:
            return family.lower()
    token = upper.split("_")[0] if "_" in upper else upper
    if token in {"ESP2UNIT", "EMS2UNIT", "MOV2UNIT", "ESP2CORP", "WMS"}:
        return token.lower()
    return "ems2unit"


def is_multi_company_dsn(dsn: str) -> bool:
    """True when DSN maps to a five-source (EMPRESA) Pentaho pattern."""
    return detect_source_family(dsn) in MULTI_SOURCE_FAMILIES
