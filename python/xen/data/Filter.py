from dataclasses import dataclass

@dataclass
class NameFilter:
    include: list[str] = None
    exclude: list[str] = None
