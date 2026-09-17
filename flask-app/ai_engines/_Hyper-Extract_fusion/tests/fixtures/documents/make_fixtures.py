"""Generate binary document fixtures for the readers test suite.

Run once from the repo root:

    python tests/fixtures/documents/make_fixtures.py

The generated files are committed so the test suite does not depend on
document-writing libraries at test time (only markitdown's readers).
"""

import zipfile
from pathlib import Path

HERE = Path(__file__).parent


def make_pdf(path: Path, text: str | None) -> None:
    """Minimal one-page PDF (hand-rolled so no writer lib is needed)."""
    if text is not None:
        stream = f"BT /F1 24 Tf 72 720 Td ({text}) Tj ET".encode()
    else:
        stream = b""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
        ),
        b"<< /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 " + str(len(objects) + 1).encode() + b"\n"
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        b"trailer\n<< /Size "
        + str(len(objects) + 1).encode()
        + b" /Root 1 0 R >>\nstartxref\n"
        + str(xref_pos).encode()
        + b"\n%%EOF\n"
    )
    path.write_bytes(out)


def make_docx(path: Path, text: str) -> None:
    """Minimal OOXML Word document (readable by mammoth)."""
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>" + text + "</w:t></w:r></w:p></w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)


def make_xlsx(path: Path, sheet: str, cell: str) -> None:
    """One-cell workbook written with openpyxl."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = sheet
    ws["A1"] = cell
    wb.save(path)


def main() -> None:
    make_pdf(HERE / "sample.pdf", "Hello Hyper Extract from PDF")
    make_pdf(HERE / "blank.pdf", None)  # no text layer -> scanned-PDF error path
    make_docx(HERE / "sample.docx", "Hello Hyper Extract from DOCX")
    make_xlsx(HERE / "sample.xlsx", "Sheet1", "Hello Hyper Extract from XLSX")
    (HERE / "sample.html").write_text(
        "<html><body><h1>Hello Hyper Extract</h1>"
        "<p>Paragraph from HTML.</p></body></html>",
        encoding="utf-8",
    )
    for f in sorted(HERE.glob("*")):
        if f.name != Path(__file__).name:
            print(f"{f.name}: {f.stat().st_size} bytes")


if __name__ == "__main__":
    main()
