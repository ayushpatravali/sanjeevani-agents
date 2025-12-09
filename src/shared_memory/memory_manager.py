"""
Thread-safe in-memory cache for:
• Fast plant look-ups
• User session context
• Agent logs + performance metrics
"""
from collections import defaultdict
from datetime import datetime
from threading import Lock
import time, uuid, logging
logger = logging.getLogger(__name__)

class SharedMemoryManager:
    def __init__(self):
        self._lock            = Lock()
        self._plant_basics    = {}                 # plant_id -> {name,…}
        self._user_sessions   = {}                 # session_id -> {...}
        self._system_logs     = []                 # capped at 1 000
        self._agent_metrics   = defaultdict(dict)  # agent -> stats

    # -------- plant basics --------
    def load_plant_basics(self, plants: list[dict]) -> None:
        with self._lock:
            self._plant_basics = {
                p["id"]: {
                    "plant_id": p["id"],
                    "botanical_name": p.get("botanical_name", "Unknown"),
                    "common_names":  p.get("common_names", []),
                    "family":        p.get("family", "Unknown"),
                    "loaded_at":     datetime.now().isoformat()
                } for p in plants
            }

    def search_plants_by_name(self, term: str) -> list[dict]:
        term = term.lower()
        with self._lock:
            return [
                v for v in self._plant_basics.values()
                if term in v["botanical_name"].lower()
                or any(term in n.lower() for n in v["common_names"])
            ]

    # -------- sessions --------
    def create_session(self, user_id: str | None = None) -> str:
        sid = uuid.uuid4().hex
        with self._lock:
            self._user_sessions[sid] = {
                "session_id": sid,
                "user_id": user_id or "anonymous",
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "query_history": []
            }
        return sid

    def add_query(self, sid: str, q: str, resp: dict) -> None:
        with self._lock:
            if sid in self._user_sessions:
                self._user_sessions[sid]["query_history"].append({
                    "ts": datetime.now().isoformat(),
                    "query": q, "response": resp
                })
                self._user_sessions[sid]["last_active"] = datetime.now().isoformat()

    # -------- logging & metrics --------
    def log_agent(self, agent: str, q: str, summary: str,
                  t: float, ok: bool) -> None:
        entry = dict(
            ts=datetime.now().isoformat(), agent=agent,
            query=q[:80] + ("…" if len(q) > 80 else ""),
            summary=summary, ms=round(t*1000, 1), success=ok
        )
        with self._lock:
            self._system_logs.append(entry)
            self._system_logs = self._system_logs[-1000:]

    def update_metrics(self, agent: str, **kv) -> None:
        with self._lock:
            self._agent_metrics[agent].update(kv)

shared_memory = SharedMemoryManager()
