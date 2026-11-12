"""
核心資料模型與 SQLite WAL 資料庫結構定義 (radar/models.py)
只讀量化比價架構：5 家參考指標 vs. 2 家可投注盤口
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

# 5 家參考指標 (產出真實勝率基準)
BENCHMARK_SOURCES = [
    {"key": "polymarket", "name": "Polymarket", "short": "Poly", "weight": 1.0, "type": "prediction"},
    {"key": "kalshi", "name": "Kalshi", "short": "Kalshi", "weight": 0.9, "type": "prediction"},
    {"key": "pinnacle", "name": "Pinnacle", "short": "PIN", "weight": 1.4, "type": "sharp_book"},
    {"key": "betfair", "name": "Betfair Exchange", "short": "BFX", "weight": 1.3, "type": "exchange"},
    {"key": "bet365", "name": "Bet365", "short": "B365", "weight": 0.9, "type": "bookmaker"},
]
BENCHMARK_WEIGHTS = {b["key"]: b["weight"] for b in BENCHMARK_SOURCES}
TOTAL_BENCHMARKS = len(BENCHMARK_SOURCES)  # 5

# 2 家實際可投注目標盤口
TARGET_BOOKS = [
    {"key": "tsl", "name": "台灣運彩", "short": "運彩", "currency": "TWD"},
    {"key": "sportsbet", "name": "澳洲 Sportsbet", "short": "SB", "currency": "AUD"},
]


@dataclass
class SourceOddsQuote:
    """單一平台對某一場特定盤口（獨贏 / 讓分 / 大小）之原始與去水後數據"""
    source: str                     # polymarket, kalshi, pinnacle, betfair, bet365, tsl, sportsbet
    league: str                     # NBA, MLB, NPB, CPBL, EPL, UCL, LOL, NHL
    sport: str                      # basketball, baseball, soccer, esports, hockey
    home_team: str                  # Canonical English team name (or display name)
    away_team: str
    home_team_zh: str = ""
    away_team_zh: str = ""
    start_time: str = ""            # ISO UTC or Taiwan UTC+8 string
    market_type: str = "ML"         # ML (獨贏), SPREAD (讓分), TOTAL (大小)
    line: Optional[float] = None    # 主隊讓分線 (e.g. -1.5) 或 大小分線 (e.g. 221.5)
    outcome_names: List[str] = field(default_factory=list)   # 2-way: [Home, Away] / [Over, Under]; 3-way: [Home, Draw, Away]
    raw_odds: List[float] = field(default_factory=list)      # 小數賠率
    true_probs: List[float] = field(default_factory=list)    # 去水後真實勝率 (0.0~1.0)
    fair_odds: List[float] = field(default_factory=list)
    vig_pct: float = 0.0
    is_live: bool = False
    # 台灣運彩專屬欄位：是否可單場投注；False 代表需串關 (⚠️ 需串關)
    single_game_allowed: Optional[bool] = None
    min_parlay_legs: int = 1
    match_url: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


RADAR_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS radar_comparisons (
    card_id TEXT PRIMARY KEY,
    match_key TEXT NOT NULL,
    sport TEXT NOT NULL,
    league TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_team_zh TEXT NOT NULL,
    away_team_zh TEXT NOT NULL,
    start_time_tw TEXT NOT NULL,
    is_live INTEGER DEFAULT 0,
    market_type TEXT NOT NULL,         -- ML / SPREAD / TOTAL
    line_display TEXT DEFAULT '',      -- e.g. "-4.5" or "221.5"
    target_book TEXT NOT NULL,         -- tsl / sportsbet
    target_book_name TEXT NOT NULL,    -- 台灣運彩 / 澳洲 Sportsbet
    selection_name TEXT NOT NULL,      -- 推薦投注選項名稱 (繁中/英文)
    selection_side TEXT NOT NULL,      -- home / away / draw / over / under
    target_odds REAL NOT NULL,         -- 目標盤口提供之賠率
    single_game_allowed INTEGER,       -- 1=可單場, 0=⚠️ 需串關, NULL=Sportsbet不適用
    min_parlay_legs INTEGER DEFAULT 1,
    valid_benchmark_count INTEGER NOT NULL,  -- 有效參考家數 (1~5)
    total_benchmarks INTEGER DEFAULT 5,
    consensus_prob REAL NOT NULL,      -- 加權共識真實勝率 (0.0~1.0)
    consensus_fair_odds REAL NOT NULL, -- 共識公平賠率
    ev_pct REAL NOT NULL,              -- 期望值 (%)
    edge_pct REAL NOT NULL,            -- 勝率優勢 (%)
    is_positive_ev INTEGER NOT NULL,   -- 1 if ev_pct > 0 else 0
    benchmarks_json TEXT NOT NULL,     -- JSON dict of all 5 benchmarks breakdown
    targets_json TEXT NOT NULL,        -- JSON dict of both target books breakdown
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_health (
    source TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL,                -- benchmark / target
    status TEXT NOT NULL,              -- ok / degraded / error
    matches_count INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    message TEXT DEFAULT '',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS radar_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_comp_ev ON radar_comparisons(ev_pct DESC);
CREATE INDEX IF NOT EXISTS idx_comp_league ON radar_comparisons(league, target_book);
"""
