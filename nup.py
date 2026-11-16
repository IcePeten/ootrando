import argparse
import contextlib
import fnmatch
import hashlib
import json
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

NO_DIR = 0xFFFFFFFF
SUPERBLOCK = struct.Struct("<4sHHQQ32sQQII16s32s")
TOC_HEADER = struct.Struct("<IIQQQQQ")
PACKAGE = struct.Struct("<QIIIIBBHIQI20s")
DIR_RECORD = struct.Struct("<IIIIQ")
FILE_RECORD = struct.Struct("<IIQQQ32sBBH12s")
KINDS = {0: "base", 1: "update", 2: "addon"}


@dataclass
class Package:
    title_id: int
    version: int
    kind: str
    root_dir: int
    exefs_dir: int
    romfs_dir: int


@dataclass
class Entry:
    path: str
    size: int
    offset: int
    stored: int
    codec: int
    sha256: bytes


@dataclass
class Nup:
    path: Path
    packages: list = field(default_factory=list)
    dirs: list = field(default_factory=list)
    files: list = field(default_factory=list)
    children: list = field(default_factory=list)
    stream: object = None

    @classmethod
    def open(cls, source):
        if hasattr(source, "read"):
            nup = cls(Path(getattr(source, "name", "game.nup")), stream=source)
        else:
            nup = cls(Path(source))
        with nup._handle() as f:
            sb = SUPERBLOCK.unpack(f.read(SUPERBLOCK.size))
            magic, _, _, toc_offset, toc_size, toc_hash, _, _, package_count, _, _, _ = sb
            if magic != b"NUP\x01":
                raise ValueError("not a NUP container")
            f.seek(toc_offset)
            toc = f.read(toc_size)
        if hashlib.sha256(toc).digest() != toc_hash:
            raise ValueError("table of contents hash mismatch")
        _, pkg_count, dir_count, file_count, pool_offset, _, _ = TOC_HEADER.unpack_from(toc, 0)
        pos = TOC_HEADER.size
        for _ in range(pkg_count):
            tid, root, exefs, romfs, version, kind, _, _, _, _, _, _ = PACKAGE.unpack_from(toc, pos)
            nup.packages.append(Package(tid, version, KINDS.get(kind, str(kind)), root, exefs, romfs))
            pos += PACKAGE.size

        def name(offset, length):
            start = pool_offset + offset
            return toc[start:start + length].decode("utf-8", "replace")

        for _ in range(dir_count):
            no, nl, first, count, _ = DIR_RECORD.unpack_from(toc, pos)
            nup.dirs.append((name(no, nl), first, count))
            pos += DIR_RECORD.size
        for _ in range(file_count):
            no, nl, size, off, stored, sha, codec, _, _, _ = FILE_RECORD.unpack_from(toc, pos)
            nup.files.append((name(no, nl), size, off, stored, codec, sha))
            pos += FILE_RECORD.size
        nup.children = list(struct.unpack_from(f"<{(pool_offset - pos) // 4}I", toc, pos))
        return nup

    def walk(self, dir_index, prefix=""):
        _, first, count = self.dirs[dir_index]
        for child in self.children[first:first + count]:
            if child < len(self.dirs):
                yield from self.walk(child, f"{prefix}{self.dirs[child][0]}/")
            else:
                n, size, off, stored, codec, sha = self.files[child - len(self.dirs)]
                yield Entry(prefix + n, size, off, stored, codec, sha)

    def package(self, kind=None):
        candidates = [p for p in self.packages if kind is None or p.kind == kind]
        if kind == "update":
            candidates.sort(key=lambda p: p.version, reverse=True)
        return candidates[0] if candidates else None

    def romfs(self, layered=True):
        """RomFS entries, with the newest update's files replacing the base game's."""
        merged = {}
        order = [self.package("base")]
        if layered and self.package("update"):
            order.append(self.package("update"))
        for pkg in order:
            if pkg and pkg.romfs_dir != NO_DIR:
                for entry in self.walk(pkg.romfs_dir):
                    merged[entry.path] = entry
        return merged

    def exefs(self):
        pkg = self.package("update") or self.package("base")
        return {e.path: e for e in self.walk(pkg.exefs_dir)} if pkg.exefs_dir != NO_DIR else {}

    def _handle(self):
        return contextlib.nullcontext(self.stream) if self.stream is not None else open(self.path, "rb")

    def read(self, entry):
        with self._handle() as f:
            f.seek(entry.offset)
            data = f.read(entry.stored)
        if entry.codec == 1:
            import zstandard
            data = zstandard.ZstdDecompressor().decompress(data, max_output_size=entry.size)
        return data


def main():
    parser = argparse.ArgumentParser(description="Inspect and extract a NUP game container")
    parser.add_argument("nup")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info")
    ls = sub.add_parser("list")
    ls.add_argument("--json")
    ex = sub.add_parser("extract")
    ex.add_argument("pattern")
    ex.add_argument("out")
    ex.add_argument("--decompress-zs", action="store_true")
    args = parser.parse_args()

    nup = Nup.open(args.nup)
    if args.cmd == "info":
        for p in nup.packages:
            print(f"{p.kind:7} {p.title_id:016X} v{p.version}")
        romfs = nup.romfs()
        print(f"{len(nup.files)} files total, {len(romfs)} in the merged RomFS, "
              f"{sum(e.size for e in romfs.values()) / 2**30:.1f} GiB")
        for path, entry in nup.exefs().items():
            print(f"  exefs/{path} {entry.size:,}")
    elif args.cmd == "list":
        rows = [{"path": e.path, "size": e.size, "zstd": e.codec == 1} for e in nup.romfs().values()]
        if args.json:
            Path(args.json).write_text(json.dumps(rows, indent=1))
        else:
            for r in rows:
                print(f"{r['size']:>12,}  {r['path']}")
    elif args.cmd == "extract":
        out = Path(args.out)
        sources = {f"romfs/{p}": e for p, e in nup.romfs().items()}
        sources.update({f"exefs/{p}": e for p, e in nup.exefs().items()})
        count = 0
        for path, entry in sources.items():
            if not fnmatch.fnmatch(path, args.pattern):
                continue
            data = nup.read(entry)
            target = out / path
            if args.decompress_zs and path.endswith(".zs"):
                import zstandard
                data = zstandard.ZstdDecompressor().decompressobj().decompress(data)
                target = target.with_suffix("")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            count += 1
        print(f"extracted {count} files to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
