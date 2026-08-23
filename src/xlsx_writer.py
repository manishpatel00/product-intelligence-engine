"""
Minimal, dependency-free XLSX writer (OOXML)
============================================
An .xlsx file is just a ZIP of XML parts. We build the smallest valid workbook
that Excel / Google Sheets / LibreOffice all open cleanly, using inline strings
(so no shared-strings table to keep in sync) and one bold header row.

Why hand-rolled? The whole engine is zero-dependency stdlib; `openpyxl` isn't
available (and PyPI is firewalled). This keeps the "runs anywhere" guarantee for
the XLSX deliverable too.

    from src.xlsx_writer import write_xlsx
    write_xlsx("out.xlsx", ["Col A", "Col B"], [{"Col A": "1", "Col B": "x"}])
"""
from __future__ import annotations
import zipfile


def _col_letter(n: int) -> str:
    """1 -> A, 26 -> Z, 27 -> AA, 252 -> IR."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _esc(v: str) -> str:
    return (v.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&apos;"))


def _cell(ref: str, value, style: int = 0) -> str:
    """Inline-string cell. Everything is written as text — catalogue values like
    '50-1/4', '120 V', leading-zero part numbers must NOT be coerced to numbers."""
    if value is None:
        value = ""
    v = _esc(str(value))
    st = f' s="{style}"' if style else ""
    if v == "":
        return f'<c r="{ref}"{st}/>'
    return f'<c r="{ref}"{st} t="inlineStr"><is><t xml:space="preserve">{v}</t></is></c>'


_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

_ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

_WORKBOOK = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Enriched" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""

_WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""

# style 0 = default, style 1 = bold (for the header row)
_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="1"><fill><patternFill patternType="none"/></fill></fills>
<borders count="1"><border/></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>
</styleSheet>"""


def _sheet_xml(headers, rows) -> str:
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>']
    # header row (bold = style 1)
    hcells = "".join(_cell(f"{_col_letter(c)}1", h, style=1) for c, h in enumerate(headers, 1))
    out.append(f'<row r="1">{hcells}</row>')
    for ri, row in enumerate(rows, start=2):
        cells = "".join(_cell(f"{_col_letter(c)}{ri}", row.get(h, "")) for c, h in enumerate(headers, 1))
        out.append(f'<row r="{ri}">{cells}</row>')
    out.append("</sheetData></worksheet>")
    return "".join(out)


def write_xlsx(path: str, headers, rows) -> str:
    """Write rows (list of dicts) under the given headers to a valid .xlsx."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _ROOT_RELS)
        z.writestr("xl/workbook.xml", _WORKBOOK)
        z.writestr("xl/_rels/workbook.xml.rels", _WORKBOOK_RELS)
        z.writestr("xl/styles.xml", _STYLES)
        z.writestr("xl/worksheets/sheet1.xml", _sheet_xml(headers, rows))
    return path
