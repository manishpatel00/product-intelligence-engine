"""
Controlled vocabularies & master-data lookups
=============================================
These encode the *rules* the Unilog reference pack specifies:

  * Placeholder values that mean "empty" (must be filtered before matching).
  * The approved Unit-of-Measure abbreviations (the ONLY permitted way to
    write a unit — always ``<number><space><unit>``, e.g. ``24 in`` not ``24in``).
  * The exact 1/64" decimal<->fraction table (Decimal_Fraction.xlsx has 63 rows).
  * A canonical manufacturer/brand map (stand-in for the 27k-row
    UniCat_Manufacturer_and_Brand_List.xlsx — swapped for the real file via
    ``load_brand_master()`` when it is present in ``data/``).
  * Distributor signal words used to catch the "Part_Manuf is a reseller, not a
    manufacturer" anomaly the Solution Guide tells us to notice.

Everything here is pure data + tiny pure helpers so the same lookups drive both
the deterministic pass and the validation gate that checks the AI's output.
"""

from __future__ import annotations
import csv
import os
import re
from math import gcd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# ---------------------------------------------------------------------------
# Placeholders — "not data"
# ---------------------------------------------------------------------------
PLACEHOLDER_VALUES = {
    "-- unbranded --", "-- no unilog brand --", "-- no dib brand --",
    "-- unbranded--", "-- no brand --", "--unbranded--",
    "n/a", "na", "none", "null", "-", "--", "",
}

def is_placeholder(val: str) -> bool:
    return val is None or val.strip().lower() in PLACEHOLDER_VALUES

def clean_placeholder(val: str) -> str:
    """Collapse any placeholder to an empty string; trim otherwise."""
    if val is None:
        return ""
    v = val.strip()
    return "" if v.lower() in PLACEHOLDER_VALUES else v

# ---------------------------------------------------------------------------
# Approved Unit-of-Measure abbreviations
# key = any spelling we might see (lowercased) -> value = approved capture form
# (representative slice of the ~500-row UOM master across 89 measurement types)
# ---------------------------------------------------------------------------
UOM_MAP = {
    # length
    "in": "in", "in.": "in", "inch": "in", "inches": "in", '"': "in", "”": "in",
    "ft": "ft", "ft.": "ft", "feet": "ft", "foot": "ft", "'": "ft", "’": "ft",
    "yd": "yd", "yard": "yd", "yards": "yd",
    "mm": "mm", "millimeter": "mm", "millimeters": "mm",
    "cm": "cm", "centimeter": "cm", "centimeters": "cm",
    "m": "m", "meter": "m", "meters": "m", "metre": "m",
    # weight
    "lb": "lb", "lbs": "lb", "lb.": "lb", "pound": "lb", "pounds": "lb", "#": "lb",
    "oz": "oz", "ounce": "oz", "ounces": "oz",
    "g": "g", "gram": "g", "grams": "g",
    "kg": "kg", "kilogram": "kg", "kilograms": "kg",
    # electrical
    "v": "V", "volt": "V", "volts": "V", "vac": "VAC", "vdc": "VDC",
    "a": "A", "amp": "A", "amps": "A", "ampere": "A", "amperes": "A",
    "ma": "mA", "milliamp": "mA",
    "w": "W", "watt": "W", "watts": "W",
    "kw": "kW", "kw-hr": "kW-hr", "kwh": "kW-hr", "hz": "Hz", "hertz": "Hz",
    "ohm": "ohm", "ohms": "ohm",
    # power / mechanical
    "hp": "HP", "horsepower": "HP",
    "rpm": "RPM",
    "nm": "N-m", "n-m": "N-m",
    "ft-lb": "ft-lb", "ftlb": "ft-lb", "ft-lbs": "ft-lb", "in-lb": "in-lb",
    # pressure / flow
    "psi": "PSI", "psig": "PSIG",
    "bar": "bar",
    "gpm": "GPM", "gph": "GPH", "cfm": "CFM", "scfm": "SCFM",
    # volume
    "gal": "gal", "gallon": "gal", "gallons": "gal",
    "qt": "qt", "quart": "qt", "quarts": "qt",
    "pt": "pt", "pint": "pt", "pints": "pt",
    "fl oz": "fl oz", "floz": "fl oz",
    "l": "L", "liter": "L", "liters": "L", "litre": "L", "ml": "mL",
    # sound / temp / angle
    "db": "dB", "dba": "dBA",
    "f": "deg F", "°f": "deg F", "deg f": "deg F", "degf": "deg F",
    "c": "deg C", "°c": "deg C", "deg c": "deg C",
    "deg": "deg", "degree": "deg", "degrees": "deg", "°": "deg",
    # counts / packaging
    "pc": "pc", "pcs": "pc", "piece": "pc", "pieces": "pc",
    "pk": "pk", "pack": "pk", "package": "pk",
    "box": "box", "bx": "box", "case": "case", "cs": "case",
    "ea": "ea", "each": "ea",
    "ct": "ct", "count": "ct",
    "roll": "roll", "rolls": "roll",
    "set": "set", "sets": "set", "kit": "kit",
    "disc": "disc", "discs": "disc", "belt": "belt", "belts": "belt",
    "sheet": "sheet", "sheets": "sheet",
    # gauge / thread
    "ga": "ga", "gauge": "ga", "awg": "AWG",
    "grit": "grit",
}

# Units that are dimensionless counts (label like "Pack Quantity"), not measures.
COUNT_UNITS = {"pc", "pk", "box", "case", "ea", "ct", "roll", "set", "kit",
               "disc", "belt", "sheet", "grit"}

def normalize_uom(raw: str):
    """'IN.' -> 'in', 'VOLTS' -> 'V'. Returns None if not an approved unit."""
    if raw is None:
        return None
    return UOM_MAP.get(raw.strip().lower(), None)

# ---------------------------------------------------------------------------
# Exact decimal<->fraction table (inch), 1/64 steps, reduced. Mirrors
# Decimal_Fraction.xlsx (1/64=0.015625 .. 63/64=0.984375).
# ---------------------------------------------------------------------------
def _build_fraction_table():
    dec2frac = {}
    for num in range(1, 64):
        dec = round(num / 64.0, 6)
        g = gcd(num, 64)
        dec2frac[dec] = f"{num // g}/{64 // g}"
    return dec2frac

DECIMAL_TO_FRACTION = _build_fraction_table()
# fast reverse for validation ("1/2" -> 0.5)
FRACTION_TO_DECIMAL = {v: k for k, v in DECIMAL_TO_FRACTION.items()}
FRACTION_TO_DECIMAL["1/1"] = 1.0

def decimal_to_fraction_inches(value: float, tol: float = 1.0 / 128):
    """0.5 -> '1/2'; 50.25 -> '50-1/4'; 24.0 -> '24'. Trade buyers search
    fractions even though manufacturers publish decimals."""
    if value is None:
        return None
    neg = value < 0
    value = abs(value)
    whole = int(value)
    frac = value - whole
    if frac < tol:
        out = str(whole)
    else:
        # nearest 1/64
        n = round(frac * 64)
        if n == 0:
            out = str(whole)
        elif n == 64:
            out = str(whole + 1)
        else:
            g = gcd(n, 64)
            frac_str = f"{n // g}/{64 // g}"
            out = f"{whole}-{frac_str}" if whole else frac_str
    return f"-{out}" if neg else out

# ---------------------------------------------------------------------------
# Canonical manufacturer / brand master (stand-in; auto-swapped for the real
# UniCat file if a CSV/xlsx export is dropped into data/).
# value = (canonical brand w/ exact casing+symbol, canonical manufacturer name)
# ---------------------------------------------------------------------------
BRAND_MASTER = {
    "3m": ("3M", "3M Company"),
    "cubitron": ("3M", "3M Company"),
    "diablo": ("Diablo", "Freud America, Inc."),
    "freud": ("Freud", "Freud America, Inc."),
    "dewalt": ("DeWalt", "Stanley Black & Decker, Inc."),
    "dcb": ("DeWalt", "Stanley Black & Decker, Inc."),
    "milwaukee": ("Milwaukee", "Milwaukee Electric Tool Corporation"),
    "makita": ("Makita", "Makita Corporation"),
    "bosch": ("Bosch", "Robert Bosch Tool Corporation"),
    "frigidaire": ("FRIGIDAIRE®", "Frigidaire"),
    "whirlpool": ("Whirlpool®", "Whirlpool Corporation"),
    "kitchenaid": ("KitchenAid®", "Whirlpool Corporation"),
    "ge": ("GE", "GE Appliances"),
    "irwin": ("IRWIN", "Irwin Industrial Tools"),
    "stanley": ("Stanley", "Stanley Black & Decker, Inc."),
    "klein": ("Klein Tools", "Klein Tools, Inc."),
    "greenlee": ("Greenlee", "Greenlee Textron Inc."),
    "ridgid": ("RIDGID", "Ridge Tool Company"),
    "craftsman": ("Craftsman", "Stanley Black & Decker, Inc."),
    "rheem": ("Rheem", "Rheem Manufacturing"),
    "moen": ("Moen", "Moen Incorporated"),
    "delta": ("Delta", "Delta Faucet Company"),
    "kohler": ("Kohler", "Kohler Co."),
}

# MPN-prefix -> (brand, series) — the stand-in for the manufacturer-source
# enrichment agent (RAG over the manufacturer's own site/catalog). Kept explicit
# so the seam is obvious; verified examples from the ground-truth pack.
MPN_PREFIX_BRAND = {
    "PDSH": ("FRIGIDAIRE®", "Professional Series"),
    "PDT": ("FRIGIDAIRE®", ""),
    "FGID": ("FRIGIDAIRE®", "Gallery Series"),
    "WDTS": ("Whirlpool®", "Eco Series"),
    "WDT": ("Whirlpool®", ""),
    "KDFM": ("KitchenAid®", ""),
    "KDTM": ("KitchenAid®", ""),
    "DCB": ("DeWalt", ""),
    "DCD": ("DeWalt", ""),
    "3MABR": ("3M", ""),
}

def load_brand_master():
    """If a real UniCat manufacturer/brand export is present in data/, index it;
    otherwise return the built-in stand-in. Looked up by lowercased brand token."""
    for fname in ("UniCat_Manufacturer_and_Brand_List.csv",
                  "unicat_manufacturer_and_brand_list.csv"):
        path = os.path.join(DATA_DIR, fname)
        if os.path.exists(path):
            master = dict(BRAND_MASTER)
            with open(path, newline="", encoding="utf-8", errors="ignore") as f:
                for row in csv.DictReader(f):
                    brand = (row.get("BRAND_NAME") or "").strip()
                    manuf = (row.get("MANUFACTURER_NAME") or "").strip()
                    if brand:
                        master[brand.lower()] = (brand, manuf or brand)
            return master
    return dict(BRAND_MASTER)

# ---------------------------------------------------------------------------
# Distributor detection — Part_Manuf is often a reseller/co-op, not the maker.
# ---------------------------------------------------------------------------
DISTRIBUTOR_SIGNAL_WORDS = {
    "cooperative", "co-op", "coop", "dealers", "dealer", "supply", "supplies",
    "wholesale", "distributors", "distribution", "distributing", "industrial supply",
    "warehouse", "reseller", "trading", "imports", "sourcing", "logistics",
}

def parse_manufacturer(part_manuf: str):
    """'Freud Inc (2435)' -> (name='Freud Inc', code='2435', is_distributor=False)."""
    part_manuf = clean_placeholder(part_manuf)
    m = re.match(r"^(.*?)\s*\(([A-Za-z0-9]+)\)\s*$", part_manuf)
    name, code = (m.group(1).strip(), m.group(2).strip()) if m else (part_manuf, "")
    low = name.lower()
    is_distributor = any(w in low for w in DISTRIBUTOR_SIGNAL_WORDS)
    return name, code, is_distributor
