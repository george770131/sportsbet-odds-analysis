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
            conn.commit()
        self.ensure_schema()

    def ensure_schema(self):
        """確保所有資料庫欄位 100% 存在 (熱遷移保證)"""
        with self.get_connection() as conn:
            # 1. 確保 matches 表欄位
            matches_cols = [
                ("live_score_home", "INTEGER DEFAULT 0"),
                ("live_score_away", "INTEGER DEFAULT 0"),
                ("live_period", "TEXT DEFAULT ''"),
                ("final_score", "TEXT DEFAULT ''")
            ]
            for col, ctype in matches_cols:
                try:
                    conn.execute(f"ALTER TABLE matches ADD COLUMN {col} {ctype}")
                except Exception:
                    pass

            # 2. 確保 live_odds 與 odds_history 欄位
            for table in ["live_odds", "odds_history"]:
                for col, ctype in [
                    ("home_handicap_line", "REAL DEFAULT -1.5"),
                    ("away_handicap_line", "REAL DEFAULT 1.5"),
                    ("handicap_home_odds", "REAL"),
                    ("handicap_away_odds", "REAL")
                ]:
                    try:
                        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ctype}")
                    except Exception:
                        pass
            conn.commit()

    # ==========================
    # 即時賽事與盤口操作
    # ==========================
    def save_match(self, match: Dict[str, Any]):
        """新增或更新即時賽事 (以台灣時間儲存)"""
        m = dict(match)
        m["updated_at"] = config.get_taiwan_now_str()
        if "live_score_home" not in m:
            m["live_score_home"] = 0
        if "live_score_away" not in m:
            m["live_score_away"] = 0
        if "live_period" not in m:
            m["live_period"] = ""
        if "final_score" not in m:
            m["final_score"] = ""

        query = """
        INSERT INTO matches (
            id, sport, league, home_team, away_team, start_time, status, favorite_team,
            live_score_home, live_score_away, live_period, final_score, updated_at
        )
        VALUES (
            :id, :sport, :league, :home_team, :away_team, :start_time, :status, :favorite_team,
            :live_score_home, :live_score_away, :live_period, :final_score, :updated_at
        )
        ON CONFLICT(id) DO UPDATE SET
            status=excluded.status,
            favorite_team=excluded.favorite_team,
            live_score_home=excluded.live_score_home,
            live_score_away=excluded.live_score_away,
            live_period=excluded.live_period,
            final_score=excluded.final_score,
            updated_at=:updated_at;
        """
        with self.get_connection() as conn:
            conn.execute(query, m)
            conn.commit()

    def save_live_odds(self, odds_data: Dict[str, Any]):
        """儲存即時賠率並記錄至走勢歷史 (以台灣時間儲存)"""
        now_tw = config.get_taiwan_now_str()
        data = dict(odds_data)
        if "home_handicap_line" not in data:
            data["home_handicap_line"] = data.get("handicap_line", -1.5)
        if "away_handicap_line" not in data:
            data["away_handicap_line"] = -data["home_handicap_line"]
        if "handicap_line" not in data:
            data["handicap_line"] = data["home_handicap_line"]
        data["updated_at"] = now_tw
        data["timestamp"] = now_tw

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
            :total_line, :over_odds, :under_odds, :updated_at
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
            updated_at=:updated_at;
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
            :timestamp
        );
        """
        with self.get_connection() as conn:
            conn.execute(upsert_query, data)
            conn.execute(history_query, data)
            conn.commit()

    def get_live_matches_with_odds(self, sport: Optional[str] = None, league: Optional[str] = None) -> pd.DataFrame:
        """取得包含最新 4 大來源 (Sportsbet, Polymarket, Kalshi, Oddsportal) 賠率的即時賽事列表"""
        self.ensure_schema()
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
            COALESCE(m.live_score_home, 0) AS live_score_home,
            COALESCE(m.live_score_away, 0) AS live_score_away,
            COALESCE(m.live_period, '') AS live_period,
            COALESCE(m.final_score, '') AS final_score,
            -- 1. 澳洲 Sportsbet
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
            -- 2. Polymarket
            poly.home_odds AS poly_home_odds,
            poly.away_odds AS poly_away_odds,
            COALESCE(poly.home_handicap_line, -1.5) AS poly_h_handicap_line,
            COALESCE(poly.away_handicap_line, 1.5) AS poly_a_handicap_line,
            poly.handicap_home_odds AS poly_h_spread_odds,
            poly.handicap_away_odds AS poly_a_spread_odds,
            poly.total_line AS poly_total_line,
            poly.over_odds AS poly_over_odds,
            poly.under_odds AS poly_under_odds,
            -- 3. Kalshi
            kalshi.home_odds AS kalshi_home_odds,
            kalshi.away_odds AS kalshi_away_odds,
            COALESCE(kalshi.home_handicap_line, -1.5) AS kalshi_h_handicap_line,
            COALESCE(kalshi.away_handicap_line, 1.5) AS kalshi_a_handicap_line,
            kalshi.handicap_home_odds AS kalshi_h_spread_odds,
            kalshi.handicap_away_odds AS kalshi_a_spread_odds,
            kalshi.total_line AS kalshi_total_line,
            kalshi.over_odds AS kalshi_over_odds,
            kalshi.under_odds AS kalshi_under_odds,
            -- 4. Oddsportal
            COALESCE(op.home_odds, op2.home_odds) AS op_home_odds,
            COALESCE(op.away_odds, op2.away_odds) AS op_away_odds,
            COALESCE(op.home_handicap_line, op2.home_handicap_line, -1.5) AS op_h_handicap_line,
            COALESCE(op.away_handicap_line, op2.away_handicap_line, 1.5) AS op_a_handicap_line,
            COALESCE(op.handicap_home_odds, op2.handicap_home_odds) AS op_h_spread_odds,
            COALESCE(op.handicap_away_odds, op2.handicap_away_odds) AS op_a_spread_odds,
            COALESCE(op.total_line, op2.total_line) AS op_total_line,
            COALESCE(op.over_odds, op2.over_odds) AS op_over_odds,
            COALESCE(op.under_odds, op2.under_odds) AS op_under_odds
        FROM matches m
        LEFT JOIN live_odds sb ON m.id = sb.match_id AND sb.bookmaker = 'Sportsbet'
        LEFT JOIN live_odds poly ON m.id = poly.match_id AND poly.bookmaker = 'Polymarket'
        LEFT JOIN live_odds kalshi ON m.id = kalshi.match_id AND kalshi.bookmaker = 'Kalshi'
        LEFT JOIN live_odds op ON m.id = op.match_id AND op.bookmaker = 'Oddsportal'
        LEFT JOIN live_odds op2 ON m.id = op2.match_id AND op2.bookmaker = 'OddsportalConsensus'
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
            try:
                return pd.read_sql_query(query, conn, params=params)
            except Exception as e:
                self.ensure_schema()
                try:
                    return pd.read_sql_query(query, conn, params=params)
                except Exception:
                    fallback_q = "SELECT m.id AS match_id, m.sport, m.league, m.home_team, m.away_team, m.start_time, m.status, m.favorite_team FROM matches m"
                    df = pd.read_sql_query(fallback_q, conn)
                    for col in [
                        "live_score_home", "live_score_away", "live_period", "final_score",
                        "sb_home_odds", "sb_away_odds", "sb_h_handicap_line", "sb_a_handicap_line", "sb_h_spread_odds", "sb_a_spread_odds", "sb_total_line", "sb_over_odds", "sb_under_odds", "odds_updated_at",
                        "poly_home_odds", "poly_away_odds", "poly_h_handicap_line", "poly_a_handicap_line", "poly_h_spread_odds", "poly_a_spread_odds", "poly_total_line", "poly_over_odds", "poly_under_odds",
                        "kalshi_home_odds", "kalshi_away_odds", "kalshi_h_handicap_line", "kalshi_a_handicap_line", "kalshi_h_spread_odds", "kalshi_a_spread_odds", "kalshi_total_line", "kalshi_over_odds", "kalshi_under_odds",
                        "op_home_odds", "op_away_odds", "op_h_handicap_line", "op_a_handicap_line", "op_h_spread_odds", "op_a_spread_odds", "op_total_line", "op_over_odds", "op_under_odds"
                    ]:
                        if col not in df.columns:
                            df[col] = ""
                    return df

    def get_match_all_sources_table(self, match_id: str) -> pd.DataFrame:
        """
        取得特定賽事的 4 大來源賠率對照表 (Sportsbet, Polymarket, Kalshi, Oddsportal)
        回傳結構化 DataFrame 用於前端表格化呈現
        """
        query = """
        SELECT bookmaker, market_type, home_odds, away_odds,
               home_handicap_line, away_handicap_line,
               handicap_home_odds, handicap_away_odds,
               total_line, over_odds, under_odds, updated_at
        FROM live_odds
        WHERE match_id = ?
        """
        sources_meta = [
            ("Sportsbet", "🇦🇺 澳洲 Sportsbet", "傳統合法博彩"),
            ("Polymarket", "🟣 Polymarket", "去中心化預測市場"),
            ("Kalshi", "🟢 Kalshi", "CFTC 合規預測市場"),
            ("Oddsportal", "🌐 Oddsportal", "全球博彩共識")
        ]
        
        with self.get_connection() as conn:
            raw_df = pd.read_sql_query(query, conn, params=[match_id])

        records = []
        for key, display_name, stype in sources_meta:
            row = raw_df[raw_df["bookmaker"] == key]
            if row.empty and key == "Oddsportal":
                row = raw_df[raw_df["bookmaker"] == "OddsportalConsensus"]

            if not row.empty:
                r = row.iloc[0]
                h_ml = float(r["home_odds"]) if pd.notna(r["home_odds"]) and r["home_odds"] > 0 else 0.0
                a_ml = float(r["away_odds"]) if pd.notna(r["away_odds"]) and r["away_odds"] > 0 else 0.0
                h_line = float(r["home_handicap_line"]) if pd.notna(r["home_handicap_line"]) else -1.5
                a_line = float(r["away_handicap_line"]) if pd.notna(r["away_handicap_line"]) else 1.5
                h_sp = float(r["handicap_home_odds"]) if pd.notna(r["handicap_home_odds"]) and r["handicap_home_odds"] > 0 else 0.0
                a_sp = float(r["handicap_away_odds"]) if pd.notna(r["handicap_away_odds"]) and r["handicap_away_odds"] > 0 else 0.0
                tot_line = float(r["total_line"]) if pd.notna(r["total_line"]) and r["total_line"] > 0 else 8.5
                o_odds = float(r["over_odds"]) if pd.notna(r["over_odds"]) and r["over_odds"] > 0 else 0.0
                u_odds = float(r["under_odds"]) if pd.notna(r["under_odds"]) and r["under_odds"] > 0 else 0.0
                
                # 計算抽水率 Overround / Margin
                vig_pct = 0.0
                if h_ml > 1.0 and a_ml > 1.0:
                    vig_pct = round(((1.0 / h_ml) + (1.0 / a_ml) - 1.0) * 100, 2)
                    
                # 隱含勝率
                h_prob = round((1.0 / h_ml) / ((1.0 / h_ml) + (1.0 / a_ml)) * 100, 1) if h_ml > 1.0 and a_ml > 1.0 else 50.0
                a_prob = round(100.0 - h_prob, 1)
                
                records.append({
                    "來源代碼": key,
                    "賠率來源 (Source)": display_name,
                    "市場類型": stype,
                    "主隊獨贏 (Home ML)": h_ml,
                    "客隊獨贏 (Away ML)": a_ml,
                    "主隊隱含勝率": f"{h_prob}%",
                    "客隊隱含勝率": f"{a_prob}%",
                    "主隊讓分盤口": f"[{h_line:+.1f}] @ {h_sp}",
                    "客隊讓分盤口": f"[{a_line:+.1f}] @ {a_sp}",
                    "大小分 (Totals)": f"{tot_line} (大: {o_odds} / 小: {u_odds})",
                    "抽水率/價差": f"{vig_pct:+.1f}%" if vig_pct != 0.0 else "--",
                    "連線狀態": "🟢 即時連線"
                })
            else:
                # 缺漏資料防呆預設
                records.append({
                    "來源代碼": key,
                    "賠率來源 (Source)": display_name,
                    "市場類型": stype,
                    "主隊獨贏 (Home ML)": 0.0,
                    "客隊獨贏 (Away ML)": 0.0,
                    "主隊隱含勝率": "--",
                    "客隊隱含勝率": "--",
                    "主隊讓分盤口": "--",
                    "客隊讓分盤口": "--",
                    "大小分 (Totals)": "--",
                    "抽水率/價差": "--",
                    "連線狀態": "🟡 撮合中"
                })
                
        return pd.DataFrame(records)

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
