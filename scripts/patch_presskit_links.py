from pathlib import Path
import re, sys

p = Path(sys.argv[1] if len(sys.argv) > 1 else "press-kit.pdf")
data = p.read_bytes()

listen = b"https://share.bridge.audio/slaven-ljujic/tribevibers-volume-one?id=30d77b92-efa8-410f-a820-8add309bebb5"
press = b"https://share.bridge.audio/slaven-ljujic/tribevibers-volume-one?id=b6d905b0-528c-4881-9399-b86cca76686d&pid=dc4e1c96-31d1-42c7-93cf-1c9e055166c4"

# If the exact two requested annotation URLs already exist in the latest objects, do nothing.
tail = data[-10000:]
if listen in tail and press in tail:
    print("PDF links already fixed")
    raise SystemExit(0)

m = re.search(br"startxref\s+(\d+)\s+%%EOF\s*$", data)
if not m:
    raise SystemExit("Cannot find final startxref")
prev = int(m.group(1))

trailer_match = re.search(br"trailer\s*<<(.*?)>>\s*startxref\s+\d+\s+%%EOF\s*$", data, re.S)
if not trailer_match:
    raise SystemExit("Cannot find final trailer")
tr = trailer_match.group(1)

size_m = re.search(br"/Size\s+(\d+)", tr)
root_m = re.search(br"/Root\s+(\d+)\s+(\d+)\s+R", tr)
id_m = re.search(br"/ID\s*\[(<[^>]+>)\s*(<[^>]+>)\]", tr)
if not (size_m and root_m):
    raise SystemExit("Cannot parse trailer")
size = int(size_m.group(1))
root_obj, root_gen = int(root_m.group(1)), int(root_m.group(2))

obj17 = b"17 0 obj\n<< /A << /S /URI /Type /Action /URI (" + listen + b") >> /Border [0 0 0] /Rect [614 78 776 114] /Subtype /Link /Type /Annot >>\nendobj\n"
obj42 = b"42 0 obj\n<< /A << /S /URI /Type /Action /URI (" + press + b") >> /Border [0 0 0] /Rect [325.9449 76 515.9449 110] /Subtype /Link /Type /Annot >>\nendobj\n"

base = data + (b"\n" if not data.endswith(b"\n") else b"")
off17 = len(base)
base += obj17
off42 = len(base)
base += obj42
xref_off = len(base)

trailer = f"<< /Size {size} /Root {root_obj} {root_gen} R /Prev {prev}".encode()
if id_m:
    trailer += b" /ID [" + id_m.group(1) + id_m.group(2) + b"]"
trailer += b" >>"

append = (
    b"xref\n17 1\n" + f"{off17:010d} 00000 n \n".encode() +
    b"42 1\n" + f"{off42:010d} 00000 n \n".encode() +
    b"trailer\n" + trailer + b"\nstartxref\n" +
    str(xref_off).encode() + b"\n%%EOF\n"
)
p.write_bytes(base + append)
print("Patched only PDF link annotations 17 and 42")
