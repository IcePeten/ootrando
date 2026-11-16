import struct


class U32(int):
    pass


class I64(int):
    pass


class U64(int):
    pass


class F64(float):
    pass


class Hash32(dict):
    pass


class Hash64(dict):
    pass


class Aligned(bytes):
    def __new__(cls, data, align):
        obj = super().__new__(cls, data)
        obj.align = align
        return obj


STRING, BINARY, ALIGNED, ARRAY, DICT, STRTAB = 0xA0, 0xA1, 0xA2, 0xC0, 0xC1, 0xC2
HASH32, HASH64 = 0x20, 0x21
BOOL, INT, FLOAT, UINT, INT64, UINT64, DOUBLE, NULL = 0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xFF
CONTAINERS = {ARRAY, DICT, HASH32, HASH64}


def _align(n, a=4):
    return (n + a - 1) // a * a


class Reader:
    def __init__(self, data):
        self.d = data
        magic = data[:2]
        if magic == b"YB":
            self.e = "<"
        elif magic == b"BY":
            self.e = ">"
        else:
            raise ValueError("not BYML")
        self.version, keys_off, strs_off, root_off = struct.unpack_from(self.e + "HIII", data, 2)
        self.keys = self._strtab(keys_off)
        self.strs = self._strtab(strs_off)
        self.root = self._node(data[root_off], root_off) if root_off else None

    def u(self, fmt, off):
        return struct.unpack_from(self.e + fmt, self.d, off)[0]

    def _header(self, off):
        word = self.u("I", off)
        if self.e == "<":
            return word & 0xFF, word >> 8
        return word >> 24, word & 0xFFFFFF

    def _strtab(self, off):
        if not off:
            return []
        t, count = self._header(off)
        if t != STRTAB:
            raise ValueError(f"expected string table at {off:#x}, got {t:#x}")
        offs = [self.u("I", off + 4 + 4 * i) for i in range(count + 1)]
        out = []
        for i in range(count):
            start = off + offs[i]
            end = self.d.index(b"\0", start)
            out.append(self.d[start:end].decode("utf-8"))
        return out

    def _value(self, t, raw):
        if t == STRING:
            return self.strs[raw]
        if t == BOOL:
            return bool(raw)
        if t == INT:
            return struct.unpack(self.e + "i", struct.pack(self.e + "I", raw))[0]
        if t == FLOAT:
            return struct.unpack(self.e + "f", struct.pack(self.e + "I", raw))[0]
        if t == UINT:
            return U32(raw)
        if t == INT64:
            return I64(self.u("q", raw))
        if t == UINT64:
            return U64(self.u("Q", raw))
        if t == DOUBLE:
            return F64(self.u("d", raw))
        if t == BINARY:
            size = self.u("I", raw)
            return bytes(self.d[raw + 4:raw + 4 + size])
        if t == ALIGNED:
            size = self.u("I", raw)
            align = self.u("I", raw + 4)
            return Aligned(self.d[raw + 8:raw + 8 + size], align)
        if t == NULL:
            return None
        if t in CONTAINERS:
            return self._node(t, raw)
        raise ValueError(f"unknown BYML node type {t:#x}")

    def _node(self, t, off):
        t2, count = self._header(off)
        if t2 != t:
            raise ValueError(f"node type mismatch at {off:#x}: {t:#x} vs {t2:#x}")
        if t == ARRAY:
            types = self.d[off + 4:off + 4 + count]
            base = off + _align(4 + count)
            return [self._value(types[i], self.u("I", base + 4 * i)) for i in range(count)]
        if t == DICT:
            out = {}
            for i in range(count):
                p = off + 4 + 8 * i
                word = self.u("I", p)
                if self.e == "<":
                    key, vt = word & 0xFFFFFF, word >> 24
                else:
                    key, vt = word >> 8, word & 0xFF
                out[self.keys[key]] = self._value(vt, self.u("I", p + 4))
            return out
        if t in (HASH32, HASH64):
            ksize = 4 if t == HASH32 else 8
            entry = ksize + 4
            types = self.d[off + 4 + entry * count:off + 4 + entry * count + count]
            out = Hash32() if t == HASH32 else Hash64()
            for i in range(count):
                p = off + 4 + entry * i
                key = self.u("I" if ksize == 4 else "Q", p)
                out[key] = self._value(types[i], self.u("I", p + ksize))
            return out
        raise ValueError(f"unexpected container {t:#x}")


def loads(data):
    r = Reader(data)
    return r.root, r.version, r.e


def _type(v):
    if isinstance(v, bool):
        return BOOL
    if isinstance(v, str):
        return STRING
    if isinstance(v, U32):
        return UINT
    if isinstance(v, I64):
        return INT64
    if isinstance(v, U64):
        return UINT64
    if isinstance(v, int):
        return INT
    if isinstance(v, F64):
        return DOUBLE
    if isinstance(v, float):
        return FLOAT
    if isinstance(v, Aligned):
        return ALIGNED
    if isinstance(v, (bytes, bytearray)):
        return BINARY
    if isinstance(v, Hash32):
        return HASH32
    if isinstance(v, Hash64):
        return HASH64
    if isinstance(v, dict):
        return DICT
    if isinstance(v, list):
        return ARRAY
    if v is None:
        return NULL
    raise TypeError(f"cannot store {type(v).__name__} in BYML")


class Writer:
    def __init__(self, root, version=7, endian="<"):
        self.e = endian
        self.version = version
        keys, strs = set(), set()
        self._collect(root, keys, strs)
        self.keys = sorted(keys, key=lambda s: s.encode("utf-8"))
        self.strs = sorted(strs, key=lambda s: s.encode("utf-8"))
        self.key_index = {k: i for i, k in enumerate(self.keys)}
        self.str_index = {s: i for i, s in enumerate(self.strs)}
        self.root = root

    def _collect(self, v, keys, strs):
        if isinstance(v, str):
            strs.add(v)
        elif isinstance(v, (Hash32, Hash64)):
            for x in v.values():
                self._collect(x, keys, strs)
        elif isinstance(v, dict):
            for k, x in v.items():
                keys.add(k)
                self._collect(x, keys, strs)
        elif isinstance(v, list):
            for x in v:
                self._collect(x, keys, strs)

    def p(self, fmt, *args):
        return struct.pack(self.e + fmt, *args)

    def _hdr(self, t, count):
        if self.e == "<":
            return self.p("I", t | (count << 8))
        return self.p("I", (t << 24) | count)

    def _strtab(self, items):
        if not items:
            return b""
        encoded = [s.encode("utf-8") + b"\0" for s in items]
        head = 4 + 4 * (len(items) + 1)
        offs, pos = [], head
        for s in encoded:
            offs.append(pos)
            pos += len(s)
        offs.append(pos)
        out = self._hdr(STRTAB, len(items)) + b"".join(self.p("I", o) for o in offs) + b"".join(encoded)
        return out + b"\0" * (_align(len(out)) - len(out))

    def _freeze(self, v):
        t = _type(v)
        if t in (DICT, HASH32, HASH64):
            return (t, tuple((k, self._freeze(x)) for k, x in sorted(v.items(), key=lambda kv: str(kv[0]))))
        if t == ARRAY:
            return (t, tuple(self._freeze(x) for x in v))
        if t == ALIGNED:
            return (t, bytes(v), v.align)
        if t == FLOAT:
            return (t, struct.pack("<f", v))
        if t == DOUBLE:
            return (t, struct.pack("<d", v))
        return (t, v)

    def dumps(self):
        self.shared = {}
        self.buf = bytearray(16)
        keytab = self._strtab(self.keys)
        keys_off = len(self.buf) if keytab else 0
        self.buf += keytab
        strtab = self._strtab(self.strs)
        strs_off = len(self.buf) if strtab else 0
        self.buf += strtab
        root_off = self._write_container(self.root) if self.root is not None else 0
        magic = b"YB" if self.e == "<" else b"BY"
        self.buf[0:16] = magic + self.p("HIII", self.version, keys_off, strs_off, root_off)
        return bytes(self.buf)

    def _pad(self, a=4):
        self.buf += b"\0" * (_align(len(self.buf), a) - len(self.buf))

    def _inline(self, v, t):
        if t == STRING:
            return self.str_index[v]
        if t == BOOL:
            return int(v)
        if t == INT:
            return struct.unpack(self.e + "I", self.p("i", v))[0]
        if t == FLOAT:
            return struct.unpack(self.e + "I", self.p("f", v))[0]
        if t == UINT:
            return int(v)
        if t == NULL:
            return 0
        return None

    def _deferred(self, v, t):
        key = self._freeze(v)
        if key in self.shared:
            return self.shared[key]
        self.shared[key] = self._deferred_new(v, t)
        return self.shared[key]

    def _deferred_new(self, v, t):
        self._pad(8 if t in (INT64, UINT64, DOUBLE) else 4)
        off = len(self.buf)
        if t == INT64:
            self.buf += self.p("q", v)
        elif t == UINT64:
            self.buf += self.p("Q", v)
        elif t == DOUBLE:
            self.buf += self.p("d", v)
        elif t == BINARY:
            self.buf += self.p("I", len(v)) + bytes(v)
            self._pad()
        elif t == ALIGNED:
            self.buf += self.p("II", len(v), v.align) + bytes(v)
            self._pad()
        return off

    def _write_container(self, v):
        key = self._freeze(v)
        if key in self.shared:
            return self.shared[key]
        off = self._write_container_new(v)
        self.shared[key] = off
        return off

    def _write_container_new(self, v):
        t = _type(v)
        self._pad()
        off = len(self.buf)
        if t == ARRAY:
            types = [_type(x) for x in v]
            self.buf += self._hdr(ARRAY, len(v)) + bytes(types)
            self._pad()
            slots = len(self.buf)
            self.buf += b"\0" * (4 * len(v))
            items = list(zip(range(len(v)), v, types))
            slot_at = lambda i: slots + 4 * i
        elif t == DICT:
            items_sorted = sorted(v.items(), key=lambda kv: self.key_index[kv[0]])
            self.buf += self._hdr(DICT, len(v))
            entries = len(self.buf)
            for k, x in items_sorted:
                xt = _type(x)
                if self.e == "<":
                    self.buf += self.p("I", self.key_index[k] | (xt << 24)) + b"\0" * 4
                else:
                    self.buf += self.p("I", (self.key_index[k] << 8) | xt) + b"\0" * 4
            items = [(i, x, _type(x)) for i, (k, x) in enumerate(items_sorted)]
            slot_at = lambda i: entries + 8 * i + 4
        elif t in (HASH32, HASH64):
            ksize = 4 if t == HASH32 else 8
            pairs = sorted(v.items())
            self.buf += self._hdr(t, len(v))
            entries = len(self.buf)
            for k, x in pairs:
                self.buf += self.p("I" if ksize == 4 else "Q", k) + b"\0" * 4
            self.buf += bytes(_type(x) for _, x in pairs)
            self._pad()
            items = [(i, x, _type(x)) for i, (k, x) in enumerate(pairs)]
            slot_at = lambda i: entries + (ksize + 4) * i + ksize
        else:
            raise TypeError("root must be a container")
        for i, x, xt in items:
            raw = self._inline(x, xt)
            if raw is None:
                raw = self._write_container(x) if xt in CONTAINERS else self._deferred(x, xt)
            struct.pack_into(self.e + "I", self.buf, slot_at(i), raw)
        return off


def dumps(root, version=7, endian="<"):
    return Writer(root, version, endian).dumps()
