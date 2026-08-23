"""
Deterministic normalization & spec-enforcement
==============================================
The AI stage *proposes* values; this module *enforces* the Unilog written
standard on them before anything ships. Because it is pure and rule-based
(not another LLM call), it is the trustworthy gate the architecture leans on:

  * every unit is rewritten to the approved abbreviation with a single space
    between number and unit  ("24in" / "24 IN." -> "24 in");
  * inch decimals are converted to the fractions trade buyers search for
    ("0.5 in" -> "1/2 in", "50.25 in" -> "50-1/4 in");
  * character limits and casing rules per field are applied and reported.
"""

from __future__ import annotations
import re
from .lookups import (UOM_MAP, COUNT_UNITS, normalize_uom,
                      decimal_to_fraction_inches, FRACTION_TO_DECIMAL)

# a number: integer, decimal, fraction (1/2), or mixed (50-1/4)
_NUM = r"\d+(?:-\d+/\d+|/\d+|\.\d+)?"
# alternation of every spelling we know, longest first so 'inches' beats 'in'
_UNIT_ALT = "|".join(sorted((re.escape(u) for u in UOM_MAP), key=len, reverse=True))
_NUM_UNIT_RE = re.compile(rf"({_NUM})\s*({_UNIT_ALT})(?![A-Za-z])", re.IGNORECASE)


def _num_to_value(num_str: str):
    """'50-1/4' -> 50.25 ; '1/2' -> 0.5 ; '24' -> 24.0 ; '3.5' -> 3.5."""
    num_str = num_str.strip()
    m = re.match(r"^(\d+)-(\d+)/(\d+)$", num_str)
    if m:
        w, n, d = map(int, m.groups())
        return w + n / d
    m = re.match(r"^(\d+)/(\d+)$", num_str)
    if m:
        n, d = map(int, m.groups())
        return n / d if d else None
    try:
        return float(num_str)
    except ValueError:
        return None


def format_measure(num_str: str, approved_unit: str) -> str:
    """Render one number+unit pair to the house style.

    Length units in inches get decimal->fraction treatment; everything else
    keeps its numeric form. Always ``<number><space><unit>``.
    """
    val = _num_to_value(num_str)
    if approved_unit == "in" and val is not None:
        num_out = decimal_to_fraction_inches(val)
    else:
        # keep integers clean (120.0 -> 120), preserve given fraction/mixed as-is
        if re.match(r"^\d+(\.\d+)?$", num_str) and val is not None and val == int(val):
            num_out = str(int(val))
        else:
            num_out = num_str.strip()
    if approved_unit in COUNT_UNITS:
        return f"{num_out} {approved_unit}"
    return f"{num_out} {approved_unit}"


def standardize_units_in_text(text: str) -> str:
    """Find every number+unit token in a free string and rewrite it to the
    approved form. Leaves the rest of the string intact.
    '24in W x 24-1/4IN D, 120VOLTS' -> '24 in W x 24-1/4 in D, 120 V'."""
    if not text:
        return text

    def repl(m):
        num, unit = m.group(1), m.group(2)
        approved = normalize_uom(unit)
        if not approved:
            return m.group(0)
        return format_measure(num, approved)

    return _NUM_UNIT_RE.sub(repl, text)


def compress_units_in_text(text: str) -> str:
    """Compressed variant for the till-receipt INVOICE_DESC: abbreviate the unit
    to its approved token but GLUE it to the number (no space) to save
    characters, still converting inch decimals to fractions.
    '120VOLTS 15AMPS 50.25IN' -> '120V 15A 50-1/4IN'."""
    if not text:
        return text

    def repl(m):
        num, unit = m.group(1), m.group(2)
        approved = normalize_uom(unit)
        if not approved:
            return m.group(0)
        spaced = format_measure(num, approved)          # e.g. '50-1/4 in'
        return spaced.replace(" ", "", 1).upper() if approved == "in" else spaced.replace(" ", "", 1)

    return _NUM_UNIT_RE.sub(repl, text)


def standardize_measure(value, unit: str):
    """(value, unit) -> ('50-1/4', 'in'). Accepts numbers or numeric strings.
    Returns (value_string, approved_unit) with the unit validated/normalized."""
    approved = normalize_uom(unit) if unit else None
    if isinstance(value, (int, float)):
        num_str = (str(int(value)) if float(value) == int(value)
                   else repr(round(float(value), 6)))
    else:
        num_str = str(value).strip()
    if approved == "in":
        v = _num_to_value(num_str)
        if v is not None:
            num_str = decimal_to_fraction_inches(v)
    elif approved and re.match(r"^\d+\.0+$", num_str):
        num_str = num_str.split(".")[0]
    return num_str, (approved or (unit or "").strip())


# ---------------------------------------------------------------------------
# character-limit + casing enforcement
# ---------------------------------------------------------------------------
def enforce_limit(text: str, limit: int, upper: bool = False) -> str:
    """Trim to <= limit chars, preferring a word boundary; optional UPPER-CASE."""
    if text is None:
        text = ""
    text = re.sub(r"\s+", " ", text).strip()
    if upper:
        text = text.upper()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if " " in cut[max(0, limit - 15):]:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;-")


def collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


# ---------------------------------------------------------------------------
# validation predicates used by the confidence / review gate
# ---------------------------------------------------------------------------
_STANDALONE_NUM_UNIT = re.compile(rf"(?<![\w/.-])({_NUM})\s*({_UNIT_ALT})(?![A-Za-z])",
                                  re.IGNORECASE)

def units_are_compliant(text: str):
    """Return (ok, offenders). A unit is compliant when it is an approved token
    AND separated from its number by exactly one space ('24 in', not '24in')."""
    if not text:
        return True, []
    offenders = []
    for m in _STANDALONE_NUM_UNIT.finditer(text):
        raw_unit = m.group(2)
        approved = normalize_uom(raw_unit)
        glued = re.match(rf"^{_NUM}{re.escape(raw_unit)}$", m.group(0).replace(" ", ""))
        spaced_ok = re.match(rf"^{_NUM}\s{re.escape(raw_unit)}$", m.group(0))
        if approved is None or (approved != raw_unit) or not spaced_ok:
            # only flag when the approved form differs from what's written
            if approved is None or m.group(0) != format_measure(m.group(1), approved):
                offenders.append(m.group(0))
    return (len(offenders) == 0), offenders
