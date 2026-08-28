"""
資料庫資料表結構與 SQL 定義 (Database Models & Schemas)
"""

SCHEMA_SQL = """
-- 1. 即時 / 即將進行 / 進行中 / 已完賽賽事表
CREATE TABLE IF NOT EXISTS matches (
    id TEXT PRIMARY KEY,               -- 賽事唯一 ID (如 sb_mlb_20260826_01)
    sport TEXT NOT NULL,               -- baseball / esports
    league TEXT NOT NULL,              -- MLB, NPB, CPBL, LCK, LPL
    home_team TEXT NOT NULL,           -- 主隊 / 藍方隊伍
    away_team TEXT NOT NULL,           -- 客隊 / 紅方隊伍
    start_time TEXT NOT NULL,          -- 比賽預定開始時間 (台灣時間)
    status TEXT DEFAULT 'UPCOMING',    -- UPCOMING (未開賽), LIVE (進行中/場中), FINISHED (已完賽)
    favorite_team TEXT,                -- 盤口低賠熱門球隊
    live_score_home INTEGER DEFAULT 0, -- 主隊即時得分
    live_score_away INTEGER DEFAULT 0, -- 客隊即時得分
    live_period TEXT DEFAULT '',       -- 進行局數/局次 (例: 3局上, Game 2)
    final_score TEXT DEFAULT '',       -- 終場比分 (例: 4 - 2)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 最新即時賠率表 (各博彩公司與預測市場即時盤口)
CREATE TABLE IF NOT EXISTS live_odds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT NOT NULL,
    bookmaker TEXT NOT NULL,           -- Sportsbet, Polymarket, Kalshi, Oddsportal
    market_type TEXT NOT NULL,         -- ML (獨贏), SPREAD (讓分), TOTAL (大小)
    home_odds REAL,                    -- 主隊賠率
    away_odds REAL,                    -- 客隊賠率
    handicap_line REAL,                -- 舊讓分值 (相容性)
    home_handicap_line REAL DEFAULT -1.5, -- 主隊讓分值 (-1.5 或 +1.5)
    away_handicap_line REAL DEFAULT 1.5,  -- 客隊讓分值 (+1.5 或 -1.5)
    handicap_home_odds REAL,           -- 主隊讓分/受讓賠率
    handicap_away_odds REAL,           -- 客隊讓分/受讓賠率
    total_line REAL,                   -- 大小分基準 (例如 8.5)
    over_odds REAL,                    -- 大分賠率
    under_odds REAL,                   -- 小分賠率
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES matches(id),
    UNIQUE(match_id, bookmaker, market_type)
);

-- 3. 歷史賠率跳動紀錄表 (用於繪製走勢折線圖與跳水偵測)
CREATE TABLE IF NOT EXISTS odds_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT NOT NULL,
    bookmaker TEXT NOT NULL,
    market_type TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    home_odds REAL,
    away_odds REAL,
    handicap_line REAL,
    home_handicap_line REAL,
    away_handicap_line REAL,
    handicap_home_odds REAL,
    handicap_away_odds REAL,
    FOREIGN KEY (match_id) REFERENCES matches(id)
);

-- 4. 歷史已結束賽事庫 (用於回測與低賠讓分最佳投資區間分析)
CREATE TABLE IF NOT EXISTS historical_matches (
    id TEXT PRIMARY KEY,
    sport TEXT NOT NULL,               -- baseball / esports
    league TEXT NOT NULL,              -- MLB, NPB, CPBL, LCK, LPL
    season TEXT NOT NULL,              -- 2024, 2025, 2026
    match_date TEXT NOT NULL,          -- YYYY-MM-DD
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_score INTEGER NOT NULL,       -- 棒球得分 / 電競勝局數
    away_score INTEGER NOT NULL,       -- 棒球得分 / 電競勝局數
    winner_team TEXT NOT NULL,
    score_diff INTEGER NOT NULL,       -- 得分差 (home - away)
    favorite_team TEXT NOT NULL,       -- 獨贏低賠看好方
    favorite_is_home INTEGER NOT NULL, -- 1 若熱門為主隊, 0 為客隊
    favorite_ml_odds REAL NOT NULL,    -- 熱門隊伍收盤獨贏賠率
    underdog_ml_odds REAL NOT NULL,    -- 弱隊收盤獨贏賠率
    favorite_spread_line REAL NOT NULL,-- 讓分值 (通常 -1.5)
    favorite_spread_odds REAL NOT NULL,-- 熱門隊伍讓分收盤賠率
    underdog_spread_odds REAL NOT NULL,-- 弱隊受讓收盤賠率
    favorite_covered INTEGER NOT NULL, -- 1 代表熱門方讓分過盤 (-1.5 過盤), 0 沒過
    total_score INTEGER NOT NULL,
    total_line REAL,
    over_hit INTEGER
);

-- 索引優化
CREATE INDEX IF NOT EXISTS idx_matches_league ON matches(league);
CREATE INDEX IF NOT EXISTS idx_live_odds_match ON live_odds(match_id);
CREATE INDEX IF NOT EXISTS idx_history_match ON odds_history(match_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_historical_league_fav ON historical_matches(league, favorite_ml_odds);
"""
