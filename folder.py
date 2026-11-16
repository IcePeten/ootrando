from dataclasses import dataclass


@dataclass
class FolderEntry:
    path: str
    size: int


class FolderSource:
    def __init__(self, sizes, reader):
        self.entries = {path: FolderEntry(path, size) for path, size in sizes.items()}
        self.reader = reader

    def romfs(self, layered=True):
        return dict(self.entries)

    def read(self, entry):
        data = self.reader(entry.path)
        return data.to_bytes() if hasattr(data, "to_bytes") else bytes(data)

    def package(self, kind=None):
        return None
