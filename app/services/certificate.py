from datetime import date
from pathlib import Path
from uuid import UUID


def generate_certificate(
    output_path: Path,
    recipient_name: str,
    course: str,
    issuer: str,
    title: str,
    issue_date: date,
    completion_date: date,
    certificate_id: UUID,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "CERTIFICATE OF COMPLETION",
        "This certificate is proudly presented to",
        recipient_name,
        f"for successfully completing {course}",
        f"Issued by: {issuer}",
        f"Completion date: {completion_date.isoformat()}",
        f"Issue date: {issue_date.isoformat()}",
        f"{title} | Certificate ID: {certificate_id}",
    ]
    stream_lines = ["BT", "/F1 20 Tf", "100 520 Td"]
    for index, line in enumerate(lines):
        if index:
            stream_lines.append("0 -42 Td")
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_lines.append(f"({escaped}) Tj")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    pdf.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    output_path.write_bytes(pdf)
