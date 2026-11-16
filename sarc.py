import math
import struct
from dataclasses import dataclass

HASH_KEY = 0x65


def name_hash(name, key=HASH_KEY):
    h = 0
    for b in name.encode():
        h = (h * key + (b - 256 if b >= 128 else b)) & 0xFFFFFFFF
    return h


@dataclass
class File:
    name: str
    data: memoryview


class Sarc:
    def __init__(self, data):
        self._data = memoryview(bytes(data))
        if bytes(self._data[:4]) != b"SARC":
            raise ValueError("not a SARC archive")
        self.endian = "<" if bytes(self._data[6:8]) == b"\xff\xfe" else ">"
        e = self.endian
        _, _, _, _, self.data_offset, _, _ = struct.unpack_from(f"{e}4sHHIIHH", self._data, 0)
        _, fat_size, count, self.key = struct.unpack_from(f"{e}4sHHI", self._data, 0x14)
        nodes = 0x14 + fat_size
        names = nodes + count * 16
        _, fnt_size, _ = struct.unpack_from(f"{e}4sHH", self._data, names)
        names += fnt_size
        self._files = []
        for i in range(count):
            _, attrs, start, end = struct.unpack_from(f"{e}IIII", self._data, nodes + i * 16)
            pos = names + (attrs & 0xFFFFFF) * 4
            stop = bytes(self._data[pos:pos + 1024]).index(b"\0")
            name = bytes(self._data[pos:pos + stop]).decode()
            self._files.append(File(name, self._data[self.data_offset + start:self.data_offset + end]))
        self._by_name = {f.name: f for f in self._files}

    def get_files(self):
        return list(self._files)

    def get_file(self, name):
        return self._by_name.get(name)

def _binary_alignment(data):
    if len(data) <= 0x20:
        return 1
    bom = bytes(data[0xC:0xE])
    if bom == b"\xfe\xff":
        e = ">"
    elif bom == b"\xff\xfe":
        e = "<"
    else:
        return 1
    if struct.unpack_from(f"{e}I", data, 0x1C)[0] != len(data):
        return 1
    return 1 << data[0xE]


def _align(value, alignment):
    return (value + alignment - 1) // alignment * alignment


class SarcWriter:
    def __init__(self, endian="<", min_alignment=4):
        self.endian = endian
        self.min_alignment = min_alignment
        self.files = {}

    @classmethod
    def from_sarc(cls, sarc):
        w = cls(sarc.endian)
        for f in sarc.get_files():
            w.files[f.name] = bytes(f.data)
        return w

    def alignment_for(self, name, data):
        return math.lcm(self.min_alignment, _binary_alignment(data))

    def write(self):
        e = self.endian
        entries = sorted(((name_hash(n), n, bytes(d)) for n, d in self.files.items()), key=lambda t: t[0])
        fat = bytearray(struct.pack(f"{e}4sHHI", b"SFAT", 0xC, len(entries), HASH_KEY))
        fnt = bytearray(struct.pack(f"{e}4sHH", b"SFNT", 0x8, 0))
        alignments, offsets = [], []
        name_pos = data_pos = 0
        for h, n, d in entries:
            a = self.alignment_for(n, d)
            alignments.append(a)
            start = _align(data_pos, a)
            offsets.append(start)
            fat += struct.pack(f"{e}IIII", h, (1 << 24) | (name_pos // 4), start, start + len(d))
            data_pos = start + len(d)
            raw = n.encode() + b"\0"
            raw += b"\0" * (_align(len(raw), 4) - len(raw))
            fnt += raw
            name_pos += len(raw)
        required = 1
        for a in alignments:
            required = math.lcm(required, a)
        head = 0x14 + len(fat) + len(fnt)
        data_offset = _align(head, required)
        out = bytearray(data_offset + data_pos)
        out[0x14:0x14 + len(fat)] = fat
        out[0x14 + len(fat):head] = fnt
        for (_, _, d), start in zip(entries, offsets):
            out[data_offset + start:data_offset + start + len(d)] = d
        bom = b"\xff\xfe" if e == "<" else b"\xfe\xff"
        struct.pack_into(f"{e}4sH", out, 0, b"SARC", 0x14)
        out[6:8] = bom
        struct.pack_into(f"{e}IIHH", out, 8, len(out), data_offset, 0x0100, 0)
        return required, bytes(out)
