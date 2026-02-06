from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List
import pandas as pd


@dataclass
class Event:
    ts: str
    type: str
    data: Dict[str, Any]


class EventLogger:
    def __init__(self) -> None:
        self.events: List[Event] = []

    def log(self, event_type: str, **data: Any) -> None:
        self.events.append(Event(ts=datetime.utcnow().isoformat(), type=event_type, data=data))

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for e in self.events:
            rows.append({"ts": e.ts, "type": e.type, **e.data})
        return pd.DataFrame(rows)

    def export_csv(self, path: str) -> None:
        self.to_dataframe().to_csv(path, index=False)
