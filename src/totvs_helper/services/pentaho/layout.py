"""Spoon canvas coordinates for Pentaho job and transformation templates."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

GuiPos = Tuple[int, int]

# ems2unit / mov2unit (SV DATASUL + Select values) — referência: dtf_Item_depois.ktr
_EMS2UNIT_GUI: Dict[str, GuiPos] = {
    "BRIC": (160, 256),
    "ECOM": (240, 256),
    "ELETRO": (320, 256),
    "NORDESTE": (400, 256),
    "PHILCO": (480, 256),
    "UNIR": (288, 336),
    "Add a checksum": (432, 336),
    "Sort rows 2": (560, 336),
    "SV DATASUL": (672, 336),
    "STAGE": (288, 448),
    "Sort rows": (432, 448),
    "SV STAGE": (560, 448),
    "Merge rows (diff)": (672, 448),
    "Filter rows": (768, 448),
    "InsereData": (896, 448),
    "Insere Data": (896, 448),
    "Select values": (1024, 448),
    "Synchronize after merge": (1168, 448),
    "IDENTICAL": (768, 336),
}

# esp2unit sync direto (sem Select values / SV) — referência: dtf_BrDoctoWms.ktr
_MULTI_ESP2UNIT_GUI: Dict[str, GuiPos] = {
    "BRIC": (160, 256),
    "ECOM": (416, 256),
    "ELETRO": (224, 256),
    "NORDESTE": (288, 256),
    "PHILCO": (352, 256),
    "UNIR": (288, 336),
    "Add a checksum": (432, 336),
    "SORT TOTVS": (560, 336),
    "Sort TOTVS": (560, 336),
    "STAGE": (288, 448),
    "SORT STAGE": (416, 448),
    "Sort stage": (416, 448),
    "Merge rows (diff)": (560, 448),
    "Filter rows": (656, 448),
    "InsereData": (784, 448),
    "Insere Data": (784, 448),
    "Synchronize after merge": (912, 448),
    "IDENTICAL": (656, 336),
}

# não multi — referência: dtf_BrConferenciaRec.ktr
_NON_MULTI_GUI: Dict[str, GuiPos] = {
    "WMS": (192, 160),
    "WMS_ECOM": (352, 160),
    "VAREJO": (192, 160),
    "ECOM": (352, 160),
    "UNIR": (288, 240),
    "Add a checksum": (448, 240),
    "SORT TOTVS": (592, 240),
    "Sort TOTVS": (592, 240),
    "STAGE": (288, 336),
    "SORT STAGE": (448, 336),
    "Sort stage": (448, 336),
    "Merge rows (diff)": (592, 336),
    "Filter rows": (743, 338),
    "InsereData": (855, 338),
    "Insere Data": (855, 338),
    "Synchronize after merge": (992, 336),
    "IDENTICAL": (743, 242),
}

_JOB_START: GuiPos = (240, 352)
_JOB_TRANS: GuiPos = (416, 352)
_JOB_SUCCESS: GuiPos = (624, 352)
_JOB_ABORT: GuiPos = (624, 480)


def detect_layout_profile(body: str) -> str:
    """Choose GUI map from transformation structure."""
    if "SV DATASUL" in body:
        return "ems2unit"
    if "WMS_ECOM" in body or (
        "<name>WMS</name>" in body and "<name>BRIC</name>" not in body
    ):
        return "non_multi"
    return "multi_esp2unit"


def apply_ktr_gui_layout(
    body: str,
    source_step_names: List[str],
    *,
    multi_company: bool,
) -> str:
    """Apply canonical Spoon positions; only steps present in the KTR are updated."""
    del source_step_names, multi_company  # profile is inferred from XML
    profile = detect_layout_profile(body)
    if profile == "ems2unit":
        positions = _EMS2UNIT_GUI
    elif profile == "non_multi":
        positions = _NON_MULTI_GUI
    else:
        positions = _MULTI_ESP2UNIT_GUI

    for step_name in _list_step_names(body):
        if step_name in positions:
            body = _set_step_gui(body, step_name, *positions[step_name])
    return body


def apply_job_gui_layout(body: str, *, dtf_entry_name: str) -> str:
    """Align Start / transformation / Success / Abort on the job canvas."""
    body = _set_job_entry_gui(body, "Start", *_JOB_START)
    body = _set_job_entry_gui(body, dtf_entry_name, *_JOB_TRANS)
    body = _set_job_entry_gui(body, "Success", *_JOB_SUCCESS)
    body = _set_job_entry_gui(body, "Abort job", *_JOB_ABORT)
    return body


def normalize_job_transformation_entry(
    body: str, entity: str, template_entity: str
) -> str:
    """Ensure TRANS entry and hops use dtf_{Entity}, not 'Transformation'."""
    dtf_new = f"dtf_{entity}"
    legacy = {f"dtf_{template_entity}", "Transformation", template_entity}
    legacy.discard(dtf_new)

    body = re.sub(
        r"(<entry>\s*<name>)(?:Transformation|dtf_[^<]+)(</name>\s*"
        r"<description/>\s*<type>TRANS</type>)",
        rf"\g<1>{dtf_new}\2",
        body,
        count=1,
        flags=re.DOTALL | re.IGNORECASE,
    )

    for old in legacy:
        body = body.replace(f"<from>{old}</from>", f"<from>{dtf_new}</from>")
        body = body.replace(f"<to>{old}</to>", f"<to>{dtf_new}</to>")

    entry_match = re.search(
        r"<entry>\s*<name>" + re.escape(dtf_new) + r"</name>.*?<type>TRANS</type>",
        body,
        re.DOTALL | re.IGNORECASE,
    )
    if entry_match:
        entry_end = body.find("</entry>", entry_match.start())
        if entry_end != -1:
            entry_xml = body[entry_match.start() : entry_end + len("</entry>")]
            entry_xml = re.sub(
                r"<transname\s*/>",
                f"<transname>{dtf_new}</transname>",
                entry_xml,
                count=1,
                flags=re.IGNORECASE,
            )
            entry_xml = re.sub(
                r"<transname>[^<]*</transname>",
                f"<transname>{dtf_new}</transname>",
                entry_xml,
                count=1,
                flags=re.IGNORECASE,
            )
            body = body[: entry_match.start()] + entry_xml + body[entry_end + len("</entry>") :]
    return body


def _list_step_names(body: str) -> List[str]:
    return re.findall(r"<step>\s*<name>([^<]+)</name>", body, re.IGNORECASE)


def _set_step_gui(body: str, step_name: str, xloc: int, yloc: int) -> str:
    pattern = (
        rf"(<step>\s*<name>{re.escape(step_name)}</name>.*?<GUI>\s*<xloc>)\d+"
        rf"(</xloc>\s*<yloc>)\d+(</yloc>)"
    )
    repl = rf"\g<1>{xloc}\g<2>{yloc}\g<3>"
    new_body, count = re.subn(
        pattern, repl, body, count=1, flags=re.DOTALL | re.IGNORECASE
    )
    return new_body if count else body


def _set_job_entry_gui(body: str, entry_name: str, xloc: int, yloc: int) -> str:
    pattern = (
        rf"(<entry>\s*<name>{re.escape(entry_name)}</name>.*?<xloc>)\d+"
        rf"(</xloc>\s*<yloc>)\d+(</yloc>)"
    )
    repl = rf"\g<1>{xloc}\g<2>{yloc}\g<3>"
    new_body, count = re.subn(
        pattern, repl, body, count=1, flags=re.DOTALL | re.IGNORECASE
    )
    return new_body if count else body
