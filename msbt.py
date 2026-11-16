import struct


class Msbt:
    def __init__(self, data):
        self.data = bytes(data)
        if self.data[:8] != b"MsgStdBn":
            raise ValueError("not MSBT")
        self.e = "<" if self.data[8:10] == b"\xff\xfe" else ">"
        self.utf8 = self.data[0x0C] == 0
        self.encoding = "utf-8" if self.utf8 else ("utf-16-le" if self.e == "<" else "utf-16-be")
        count = struct.unpack_from(self.e + "H", self.data, 0x0E)[0]
        self.sections = []
        pos = 0x20
        for _ in range(count):
            magic = self.data[pos:pos + 4]
            size = struct.unpack_from(self.e + "I", self.data, pos + 4)[0]
            self.sections.append([magic, self.data[pos + 16:pos + 16 + size]])
            pos += 16 + size
            pos = (pos + 15) // 16 * 16
        self.labels = self._labels()
        self.texts = self._texts()

    def section(self, magic):
        return next(s for s in self.sections if s[0] == magic)

    def _labels(self):
        body = self.section(b"LBL1")[1]
        groups = struct.unpack_from(self.e + "I", body, 0)[0]
        out = {}
        for i in range(groups):
            n, off = struct.unpack_from(self.e + "II", body, 4 + 8 * i)
            for _ in range(n):
                ln = body[off]
                name = body[off + 1:off + 1 + ln].decode()
                idx = struct.unpack_from(self.e + "I", body, off + 1 + ln)[0]
                out[name] = idx
                off += 1 + ln + 4
        return out

    def _texts(self):
        body = self.section(b"TXT2")[1]
        n = struct.unpack_from(self.e + "I", body, 0)[0]
        offs = [struct.unpack_from(self.e + "I", body, 4 + 4 * i)[0] for i in range(n)] + [len(body)]
        return [body[offs[i]:offs[i + 1]] for i in range(n)]

    def text(self, label):
        return self.texts[self.labels[label]]

    def plain(self, raw):
        if self.utf8:
            out, i = [], 0
            while i < len(raw):
                b = raw[i]
                if b == 0x0E:
                    size = struct.unpack_from(self.e + "H", raw, i + 5)[0]
                    out.append("{tag}")
                    i += 7 + size
                elif b == 0x0F:
                    out.append("{/tag}")
                    i += 5
                elif b == 0:
                    i += 1
                else:
                    j = i
                    while j < len(raw) and raw[j] not in (0, 0x0E, 0x0F):
                        j += 1
                    out.append(raw[i:j].decode("utf-8", "replace"))
                    i = j
            return "".join(out)
        units = struct.unpack(self.e + f"{len(raw) // 2}H", raw[:len(raw) // 2 * 2])
        out, i = [], 0
        while i < len(units):
            u = units[i]
            if u == 0x0E:
                size = units[i + 3]
                out.append("{tag}")
                i += 4 + size // 2
            elif u == 0x0F:
                out.append("{/tag}")
                i += 3
            elif u == 0:
                i += 1
            else:
                out.append(chr(u))
                i += 1
        return "".join(out)

    def leading_tags(self, raw):
        i = 0
        if self.utf8:
            while i < len(raw) and raw[i] == 0x0E:
                i += 7 + struct.unpack_from(self.e + "H", raw, i + 5)[0]
            return raw[:i]
        while i + 1 < len(raw) and struct.unpack_from(self.e + "H", raw, i)[0] == 0x0E:
            i += 8 + struct.unpack_from(self.e + "H", raw, i + 6)[0]
        return raw[:i]

    def encode(self, s):
        return s.encode(self.encoding) + (b"\0" if self.utf8 else b"\0\0")

    def set_text(self, label, raw):
        self.texts[self.labels[label]] = raw

    def add_text(self, label, raw):
        if label in self.labels:
            self.set_text(label, raw)
            return
        self.labels[label] = len(self.texts)
        self.texts.append(raw)
        self._added = True

    def _label_table(self):
        groups = struct.unpack_from(self.e + "I", self.section(b"LBL1")[1], 0)[0]
        buckets = [[] for _ in range(groups)]
        for name, idx in self.labels.items():
            h = 0
            for c in name.encode():
                h = (h * 0x492 + c) & 0xFFFFFFFF
            buckets[h % groups].append((name, idx))
        head = struct.pack(self.e + "I", groups)
        entries = b""
        pos = 4 + 8 * groups
        for bucket in buckets:
            head += struct.pack(self.e + "II", len(bucket), pos + len(entries))
            for name, idx in bucket:
                raw = name.encode()
                entries += bytes([len(raw)]) + raw + struct.pack(self.e + "I", idx)
        return head + entries

    def dumps(self):
        if getattr(self, "_added", False):
            self.section(b"LBL1")[1] = self._label_table()
        n = len(self.texts)
        head = 4 + 4 * n
        offs, pos = [], head
        for t in self.texts:
            offs.append(pos)
            pos += len(t)
        body = struct.pack(self.e + "I", n) + b"".join(struct.pack(self.e + "I", o) for o in offs) + b"".join(self.texts)
        self.section(b"TXT2")[1] = body
        out = bytearray(self.data[:0x20])
        for magic, sbody in self.sections:
            out += magic + struct.pack(self.e + "I", len(sbody)) + b"\0" * 8 + sbody
            out += b"\xab" * ((16 - len(out) % 16) % 16)
        struct.pack_into(self.e + "I", out, 0x12, len(out))
        return bytes(out)
