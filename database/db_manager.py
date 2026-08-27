"""
資料庫存取管理員 (Database Manager)
負責 SQLite 資料庫連線、初始化、賽事與賠率資料讀寫
"""
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import config

class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.DB_PATH
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """初始化資料表結構並自動遷移欄位"""
        from database.models import SCHEMA_SQL
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            
            # 自動檢測並補足新欄位 (Migration)
            for table in ["live_odds", "odds_history"]:
                cur = conn.execute(f"PRAGMA table_info({table})")
                cols = [row["name"] for row in cur.fetchall()]
                if "home_handicap_line" not in cols:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN home_handicap_line REAL DEFAULT -1.5")
                if "away_handicap_line" not in cols:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN away_handicap_line REAL DEFAULT 1.5")
            conn.commit()

    # ==========================
    # 即時賽事與盤口操作
    # ==========================
    def save_match(self, match: Dict[str, Any]):
        """新增或更新即時賽事"""
        query = """
        INSERT INTO matches (id, sport, league, home_team, away_team, start_time, status, favorite_team, updated_at)
        VALUES (:id, :sport, :league, :home_team, :away_team, :start_time, :status, :favorite_team, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            status=excluded.status,
            favorite_team=excluded.favorite_team,
            updated_at=CURRENT_TIMESTAMP;
        """
        with self.get_connection() as conn:
            conn.execute(query, match)
            conn.commit()

    def save_live_odds(self, odds_data: Dict[str, Any]):
        """儲存即時賠率並記錄至走勢歷史"""
        # 確保 home_handicap_line 與 away_handicap_line 存在預設值
        data = dict(odds_data)
        if "home_handicap_line" not in data:
            data["home_handicap_line"] = data.get("handicap_line", -1.5)
        if "away_handicap_line" not in data:
            data["away_handicap_line"] = -data["home_handicap_line"]
        if "handicap_line" not in data:
            data["handicap_line"] = data["home_handicap_line"]

        upsert_query = """
        INSERT INTO live_odds (
            match_id, bookmaker, market_type, home_odds, away_odds,
            handicap_line, home_handicap_line, away_handicap_line,
            handicap_home_odds, handicap_away_odds,
            total_line, over_odds, under_odds, updated_at
        ) VALUES (
            :match_id, :bookmaker, :market_type, :home_odds, :away_odds,
            :handicap_line, :home_handicap_line, :away_handicap_line,
            :handicap_home_odds, :handicap_away_odds,
            :total_line, :over_odds, :under_odds, CURRENT_TIMESTAMP
        ) ON CONFLICT(match_id, bookmaker, market_type) DO UPDATE SET
            home_odds=excluded.home_odds,
            away_odds=excluded.away_odds,
            handicap_line=excluded.handicap_line,
            home_handicap_line=excluded.home_handicap_line,
            away_handicap_line=excluded.away_handicap_line,
            handicap_home_odds=excluded.handicap_home_odds,
            handicap_away_odds=excluded.handicap_away_odds,
            total_line=excluded.total_line,
            over_odds=excluded.over_odds,
            under_odds=excluded.under_odds,
            updated_at=CURRENT_TIMESTAMP;
        """
        history_query = """
        INSERT INTO odds_history (
            match_id, bookmaker, market_type, home_odds, away_odds,
            handicap_line, home_handicap_line, away_handicap_line,
            handicap_home_odds, handicap_away_odds, timestamp
        ) VALUES (
            :match_id, :bookmaker, :market_type, :home_odds, :away_odds,
            :handicap_line, :home_handicap_line, :away_handicap_line,
            :handicap_home_odds, :handicap_away_odds,
            CURRENT_TIMESTAMP
        );
        """
        with self.get_connection() as conn:
            conn.execute(upsert_query, data)
            conn.execute(history_query, data)
            conn.commit()

    def get_live_matches_with_odds(self, sport: Optional[str] = None, league: Optional[str] = None) -> pd.DataFrame:
        """取得包含最新 Sportsbet 賠率與市場對比的即時賽事列表"""
        query = """
        SELECT 
            m.id AS match_id,
            m.sport,
            m.league,
            m.home_team,
            m.away_team,
            m.start_time,
            m.status,
            m.favorite_team,
            sb.home_odds AS sb_home_odds,
            sb.away_odds AS sb_away_odds,
            sb.handicap_line AS sb_handicap_line,
            COALESCE(sb.home_handicap_line, -1.5) AS sb_h_handicap_line,
            COALESCE(sb.away_handicap_line, 1.5) AS sb_a_handicap_line,
            sb.handicap_home_odds AS sb_h_spread_odds,
            sb.handicap_away_odds AS sb_a_spread_odds,
            sb.total_line AS sb_total_line,
            sb.over_odds AS sb_over_odds,
            sb.under_odds AS sb_under_odds,
            sb.updated_at AS odds_updated_at,
            op.home_odds AS op_home_odds,
            op.away_odds AS op_away_odds,
            COALESCE(op.home_handicap_line, -1.5) AS op_h_handicap_line,
            COALESCE(op.away_handicap_line, 1.5) AS op_a_handicap_line,
            op.handicap_home_odds AS op_h_spread_odds,
            op.handicap_away_odds AS op_a_spread_odds
        FROM matches m
        LEFT JOIN live_odds sb ON m.id = sb.match_id AND sb.bookmaker = 'Sportsbet'
        LEFT JOIN live_odds op ON m.id = op.match_id AND op.bookmaker = 'OddsportalConsensus'
        WHERE 1=1
        """
        params = []
        if sport:
            query += " AND m.sport = ?"
            params.append(sport)
        if league:
            query += " AND m.league = ?"
            params.append(league)
        query += " ORDER BY m.start_time ASC"

        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_odds_history(self, match_id: str, bookmaker: str = "Sportsbet") -> pd.DataFrame:
        """取得單場比賽的歷史賠率變動數據"""
        query = """
        SELECT timestamp, home_odds, away_odds, handicap_line, home_handicap_line, away_handicap_line, handicap_home_odds, handicap_away_odds
        FROM odds_history
        WHERE match_id = ? AND bookmaker = ?
        ORDER BY timestamp ASC
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=[match_id, bookmaker])

    # ==========================
    # 歷史已結束賽事操作 (用於回測與分析)
    # ==========================
    def insert_historical_matches(self, matches: List[Dict[str, Any]]):
        """批量匯入歷史賽事數據"""
        query = """
        INSERT OR REPLACE INTO historical_matches (
            id, sport, league, season, match_date, home_team, away_team,
            home_score, away_score, winner_team, score_diff,
            favorite_team, favorite_is_home, favorite_ml_odds, underdog_ml_odds,
            favorite_spread_line, favorite_spread_odds, underdog_spread_odds,
            favorite_covered, total_score, total_line, over_hit
        ) VALUES (
            :id, :sport, :league, :season, :match_date, :home_team, :away_team,
            :home_score, :away_score, :winner_team, :score_diff,
            :favorite_team, :favorite_is_home, :favorite_ml_odds, :underdog_ml_odds,
            :favorite_spread_line, :favorite_spread_odds, :underdog_spread_odds,
            :favorite_covered, :total_score, :total_line, :over_hit
        );
        """
        with self.get_connection() as conn:
            conn.executemany(query, matches)
            conn.commit()

    def get_historical_matches(self, sport: Optional[str] = None, league: Optional[str] = None) -> pd.DataFrame:
        """取得歷史賽事 DataFrame"""
        query = "SELECT * FROM historical_matches WHERE 1=1"
        params = []
        if sport:
            query += " AND sport = ?"
            params.append(sport)
        if league:
            query += " AND league = ?"
            params.append(league)
        query += " ORDER BY match_date DESC"

        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_db_summary(self) -> Dict[str, Any]:
        """取得資料庫統計摘要資訊"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM matches")
            total_live_matches = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM historical_matches")
            total_hist_matches = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT league) FROM historical_matches")
            total_leagues = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM odds_history")
            total_history_ticks = cursor.fetchone()[0]
            return {
                "live_matches": total_live_matches,
                "historical_matches": total_hist_matches,
                "leagues_count": total_leagues,
                "odds_ticks": total_history_ticks
            }

# 單例模式實例
db = DatabaseManager()
