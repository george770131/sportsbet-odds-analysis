"""
只讀比價雷達 SQLite (WAL 模式) 持久化管理 (radar/database.py)
支援背景採集寫入與 FastAPI 併發毫秒級讀取
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
import config
from .models import RADAR_SCHEMA_SQL

RADAR_DB_PATH = config.DATA_DIR / "radar_master.db"


class RadarDatabase:
    def __init__(self, db_path: Path = RADAR_DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=15.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(RADAR_SCHEMA_SQL)

    def replace_comparisons(self, cards: List[Dict[str, Any]]) -> None:
        """原子性替換最新比價結果卡片，確保前端任何瞬間讀到的都是一致快照"""
        with self._connect() as conn:
            conn.execute("DELETE FROM radar_comparisons")
            for c in cards:
                conn.execute(
                    """
                    INSERT INTO radar_comparisons (
                        card_id, match_key, sport, league,
                        home_team, away_team, home_team_zh, away_team_zh,
                        start_time_tw, is_live, market_type, line_display,
                        target_book, target_book_name, selection_name, selection_side,
                        target_odds, single_game_allowed, min_parlay_legs,
                        valid_benchmark_count, total_benchmarks,
                        consensus_prob, consensus_fair_odds, ev_pct, edge_pct,
                        is_positive_ev, benchmarks_json, targets_json, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        c["card_id"], c["match_key"], c["sport"], c["league"],
                        c["home_team"], c["away_team"], c["home_team_zh"], c["away_team_zh"],
                        c["start_time_tw"], 1 if c.get("is_live") else 0,
                        c["market_type"], c.get("line_display", ""),
                        c["target_book"], c["target_book_name"],
                        c["selection_name"], c["selection_side"],
                        float(c["target_odds"]),
                        None if c.get("single_game_allowed") is None else (1 if c["single_game_allowed"] else 0),
                        int(c.get("min_parlay_legs", 1)),
                        int(c["valid_benchmark_count"]), int(c.get("total_benchmarks", 5)),
                        float(c["consensus_prob"]), float(c["consensus_fair_odds"]),
                        float(c["ev_pct"]), float(c["edge_pct"]),
                        1 if c.get("is_positive_ev") else 0,
                        json.dumps(c.get("benchmarks", {}), ensure_ascii=False),
                        json.dumps(c.get("targets", {}), ensure_ascii=False),
                        c["updated_at"],
                    ),
                )

    def upsert_source_health(self, health_rows: List[Dict[str, Any]]) -> None:
        with self._connect() as conn:
            for row in health_rows:
                conn.execute(
                    """
                    INSERT INTO source_health (source, display_name, role, status, matches_count, latency_ms, message, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(source) DO UPDATE SET
                        display_name=excluded.display_name,
                        role=excluded.role,
                        status=excluded.status,
                        matches_count=excluded.matches_count,
                        latency_ms=excluded.latency_ms,
                        message=excluded.message,
                        updated_at=excluded.updated_at
                    """,
                    (
                        row["source"], row["display_name"], row["role"],
                        row["status"], int(row.get("matches_count", 0)),
                        int(row.get("latency_ms", 0)), row.get("message", ""),
                        row["updated_at"],
                    ),
                )

    def set_meta(self, key: str, value: str, updated_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO radar_meta (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, value, updated_at),
            )

    def get_comparisons(
        self,
        league: str = "ALL",
        target_book: str = "ALL",
        min_benchmarks: int = 1,
        parlay_filter: str = "ALL",  # ALL / SINGLE_ONLY / PARLAY_ONLY
        only_positive_ev: bool = False,
        min_ev: float = -50.0,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM radar_comparisons WHERE valid_benchmark_count >= ? AND ev_pct >= ?"
        params: List[Any] = [min_benchmarks, min_ev]

        if league and league.upper() != "ALL":
            query += " AND UPPER(league) = ?"
            params.append(league.upper())
        if target_book and target_book.upper() != "ALL":
            query += " AND target_book = ?"
            params.append(target_book.lower())
        if only_positive_ev:
            query += " AND is_positive_ev = 1"
        if parlay_filter == "SINGLE_ONLY":
            query += " AND (single_game_allowed IS NULL OR single_game_allowed = 1)"
        elif parlay_filter == "PARLAY_ONLY":
            query += " AND single_game_allowed = 0"

        query += " ORDER BY ev_pct DESC, valid_benchmark_count DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            d["is_live"] = bool(d["is_live"])
            d["is_positive_ev"] = bool(d["is_positive_ev"])
            d["single_game_allowed"] = None if d["single_game_allowed"] is None else bool(d["single_game_allowed"])
            d["benchmarks"] = json.loads(d.pop("benchmarks_json", "{}"))
            d["targets"] = json.loads(d.pop("targets_json", "{}"))
            results.append(d)
        return results

    def get_health_status(self) -> Dict[str, Any]:
        with self._connect() as conn:
            sources = [dict(r) for r in conn.execute("SELECT * FROM source_health ORDER BY role, source").fetchall()]
            meta_rows = conn.execute("SELECT key, value, updated_at FROM radar_meta").fetchall()
        meta = {r["key"]: {"value": r["value"], "updated_at": r["updated_at"]} for r in meta_rows}
        return {"sources": sources, "meta": meta}


radar_db = RadarDatabase()
