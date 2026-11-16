import struct

MAX_ENTRIES = 120


def _partition(f, base, size_limit):
    f.seek(base)
    head = f.read(16)
    if len(head) < 16:
        return None
    magic, count, strsize, _ = struct.unpack("<4sIII", head)
    if magic not in (b"PFS0", b"HFS0") or count > 100000 or strsize > 16 << 20:
        return None
    esize = 24 if magic == b"PFS0" else 64
    table = f.read(count * esize + strsize)
    strings = table[count * esize:]
    data_start = base + 16 + count * esize + strsize
    entries = []
    for i in range(min(count, MAX_ENTRIES)):
        off, size, noff = struct.unpack_from("<QQI", table, i * esize)
        end = strings.find(b"\0", noff)
        name = strings[noff:end if end >= 0 else len(strings)].decode("utf-8", "replace")
        entry = {"name": name, "size": size, "offset": data_start + off}
        if name.endswith(".nca") and data_start + off + 0x204 <= size_limit:
            f.seek(data_start + off + 0x200)
            entry["plain_nca"] = f.read(4) in (b"NCA2", b"NCA3", b"NCA4")
        entries.append(entry)
    return {"magic": magic.decode(), "count": count, "entries": entries}


def describe(f, size, name):
    f.seek(0)
    head = f.read(0x200)
    info = {
        "name_ext": name.rsplit(".", 1)[-1].lower() if "." in name else "",
        "size": size,
        "head": head[:32].hex(),
        "at_100": head[0x100:0x110].hex(),
        "format": "unknown",
    }
    if head[:4] == b"PFS0":
        info["format"] = "NSP/NSZ (PFS0)"
        info["root"] = _partition(f, 0, size)
    elif head[0x100:0x104] == b"HEAD":
        info["format"] = "XCI/XCZ (gamecard)"
        hfs_offset, hfs_size = struct.unpack_from("<QQ", head, 0x130)
        root = _partition(f, hfs_offset, size)
        info["root"] = root
        if root:
            info["partitions"] = {}
            for part in root["entries"]:
                info["partitions"][part["name"]] = _partition(f, part["offset"], size)
    elif head[:4] == b"NUP\x01":
        info["format"] = "NUP"
    for part in [info.get("root")] + list((info.get("partitions") or {}).values()):
        for entry in (part or {}).get("entries", []):
            entry.pop("offset", None)
    return info


def summary(info):
    kinds = {}
    parts = list(info["partitions"].values()) if info.get("partitions") else [info.get("root")]
    for part in parts:
        for entry in (part or {}).get("entries", []):
            ext = entry["name"].rsplit(".", 1)[-1].lower()
            kinds[ext] = kinds.get(ext, 0) + 1
    return ", ".join(f"{n} .{k}" for k, n in sorted(kinds.items())) or "no readable contents"
