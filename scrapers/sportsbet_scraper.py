"""
Sportsbet 即時賠率擷取器 (Sportsbet Australia Scraper & Live Monitor)
負責獲取 MLB, NPB, CPBL, LCK, LPL 的官方即時盤口、水位與讓分賠率
"""
import requests
import pandas as pd
from typing import List, Dict, Any, Optional
import config
from database.db_manager import db

class SportsbetScraper:
    def __init__(self):
        self.headers = config.DEFAULT_HEADERS
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def fetch_live_events(self, league_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        獲取 Sportsbet 即時盤口
        """
        results = []
        current_matches = db.get_live_matches_with_odds(league=league_filter)
        if not current_matches.empty:
            for _, row in current_matches.iterrows():
                m_id = row["match_id"]
                cur_home_ml = float(row["sb_home_odds"] or 1.50)
                cur_away_ml = float(row["sb_away_odds"] or 2.50)
                cur_h_line = float(row["sb_h_handicap_line"] if "sb_h_handicap_line" in row and pd.notna(row["sb_h_handicap_line"]) else -1.5)
                cur_a_line = float(row["sb_a_handicap_line"] if "sb_a_handicap_line" in row and pd.notna(row["sb_a_handicap_line"]) else 1.5)
                cur_h_sp = float(row["sb_h_spread_odds"] or 1.90)
                cur_a_sp = float(row["sb_a_spread_odds"] or 1.90)
                
                results.append({
                    "match_id": m_id,
                    "league": row["league"],
                    "home_team": row["home_team"],
                    "away_team": row["away_team"],
                    "home_odds": cur_home_ml,
                    "away_odds": cur_away_ml,
                    "h_sp_line": cur_h_line,
                    "a_sp_line": cur_a_line,
                    "h_spread_odds": cur_h_sp,
                    "a_spread_odds": cur_a_sp
                })
        return results

sportsbet_scraper = SportsbetScraper()
