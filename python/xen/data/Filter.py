from dataclasses import dataclass

@dataclass
class NameFilter:
    include: list[str]|None = None
    exclude: list[str]|None = None

@dataclass
class SongDataFilter:
    timeSignature: str = '4/4'
    instrumentName: NameFilter|None = None
    minNotesPerSequence: int = 2

