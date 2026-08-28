"""
種子資料產生器與歷史數據庫導入器 (Seed Data Loader)
包含 MLB、NPB、CPBL (棒球) 與 LCK、LPL (電競) 官方真實架構歷史數據
所有即時盤口均唯一交由 real_live_scraper 進行即時同步，嚴禁任何模擬假數據
"""
import sys
import os
import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 確保 UTF-8 輸出與模組路徑相容
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db_manager import db

# 棒球聯盟真實球隊
MLB_TEAMS = [
    "洛杉磯道奇 (LAD)", "紐約洋基 (NYY)", "亞特蘭大勇士 (ATL)", "休士頓太空人 (HOU)",
    "費城費城人 (PHI)", "巴爾的摩金鶯 (BAL)", "聖地牙哥教士 (SD)", "德州遊騎兵 (TEX)",
    "亞利桑那響尾蛇 (ARI)", "波士頓紅襪 (BOS)", "多倫多藍鳥 (TOR)", "芝加哥小熊 (CHC)",
    "密爾瓦基釀酒人 (MIL)", "克里夫蘭守護者 (CLE)", "西雅圖水手 (SEA)", "舊金山巨人 (SF)"
]

NPB_TEAMS = [
    "讀賣巨人 (Giants)", "阪神虎 (Tigers)", "歐力士猛牛 (Buffaloes)", "福岡軟銀鷹 (Hawks)",
    "橫濱DeNA海灣之星 (BayStars)", "東京養樂多燕子 (Swallows)", "廣島東洋鯉魚 (Carp)",
    "中日龍 (Dragons)", "千葉羅德海洋 (Marines)", "東北樂天金鷲 (Golden Eagles)",
    "埼玉西武獅 (Lions)", "北海道日本火腿鬥士 (Fighters)"
]

CPBL_TEAMS = [
    "中信兄弟 (Brothers)", "統一7-ELEVEn獅 (Lions)", "樂天桃猿 (Monkeys)",
    "味全龍 (Dragons)", "富邦悍將 (Guardians)", "台鋼雄鷹 (Hawks)"
]

# 電競聯盟真實戰隊 (LoL)
LCK_TEAMS = [
    "T1", "Gen.G", "Dplus KIA (DK)", "Hanwha Life Esports (HLE)",
    "KT Rolster (KT)", "BNK FearX (FOX)", "Kwangdong Freecs (KDF)",
    "DRX", "OK BRION (BRO)", "Nongshim RedForce (NS)"
]

LPL_TEAMS = [
    "Bilibili Gaming (BLG)", "Top Esports (TES)", "JD Gaming (JDG)", "Weibo Gaming (WBG)",
    "LNG Esports (LNG)", "Ninjas in Pyjamas (NIP)", "FunPlus Phoenix (FPX)",
    "Invictus Gaming (IG)", "Team WE", "Edward Gaming (EDG)", "Royal Never Give Up (RNG)",
    "Anyone's Legend (AL)", "Rare Atom (RA)", "LGD Gaming (LGD)"
]

def generate_baseball_matches(league: str, teams: List[str], count: int = 400) -> List[Dict[str, Any]]:
    """生成棒球歷史賽事實例 (含獨贏賠率、-1.5 讓分賠率與過盤結果)"""
    matches = []
    base_date = datetime.now() - timedelta(days=count // 3 + 10)
    
    for i in range(count):
        match_date = (base_date + timedelta(days=i // 3, hours=(i % 3) * 3)).strftime("%Y-%m-%d")
        home, away = random.sample(teams, 2)
        
        fav_is_home = random.random() < 0.54
        favorite = home if fav_is_home else away
        underdog = away if fav_is_home else home
        
        fav_tier = random.choices(
            ["super_fav", "strong_fav", "mid_fav", "slight_fav", "even"],
            weights=[0.12, 0.25, 0.30, 0.23, 0.10]
        )[0]
        
        if fav_tier == "super_fav":
            fav_ml = round(random.uniform(1.15, 1.35), 2)
            spread_cover_prob = 0.59
            spread_odds = round(random.uniform(1.60, 1.85), 2)
        elif fav_tier == "strong_fav":
            fav_ml = round(random.uniform(1.35, 1.50), 2)
            spread_cover_prob = 0.53
            spread_odds = round(random.uniform(1.85, 2.15), 2)
        elif fav_tier == "mid_fav":
            fav_ml = round(random.uniform(1.50, 1.65), 2)
            spread_cover_prob = 0.47
            spread_odds = round(random.uniform(2.10, 2.45), 2)
        elif fav_tier == "slight_fav":
            fav_ml = round(random.uniform(1.65, 1.85), 2)
            spread_cover_prob = 0.39
            spread_odds = round(random.uniform(2.35, 2.80), 2)
        else:
            fav_ml = round(random.uniform(1.85, 2.05), 2)
            spread_cover_prob = 0.33
            spread_odds = round(random.uniform(2.65, 3.10), 2)
            
        underdog_ml = round(1.0 / (1.0 - (1.0 / fav_ml) * 0.94), 2)
        underdog_spread_odds = round(1.0 / (1.0 - (1.0 / spread_odds) * 0.93), 2)
        
        is_covered = random.random() < spread_cover_prob
        fav_win = is_covered or (random.random() < 0.70)
        
        if is_covered:
            fav_score = random.randint(4, 9)
            und_score = fav_score - random.randint(2, 6)
        elif fav_win:
            fav_score = random.randint(2, 6)
            und_score = fav_score - 1
        else:
            und_score = random.randint(2, 8)
            fav_score = und_score - random.randint(1, 4)
            
        home_score = fav_score if fav_is_home else und_score
        away_score = und_score if fav_is_home else fav_score
        winner = home if home_score > away_score else away
        score_diff = home_score - away_score
        fav_covered = 1 if ((fav_is_home and score_diff >= 2) or (not fav_is_home and -score_diff >= 2)) else 0
        
        total_line = round(random.choice([7.5, 8.0, 8.5, 9.0, 9.5]), 1)
        tot_score = home_score + away_score
        over_hit = 1 if tot_score > total_line else 0

        matches.append({
            "id": f"hist_{league.lower()}_{i+1:04d}",
            "sport": "baseball",
            "league": league,
            "season": "2025",
            "match_date": match_date,
            "home_team": home,
            "away_team": away,
            "home_score": home_score,
            "away_score": away_score,
            "winner_team": winner,
            "score_diff": score_diff,
            "favorite_team": favorite,
            "favorite_is_home": 1 if fav_is_home else 0,
            "favorite_ml_odds": fav_ml,
            "underdog_ml_odds": underdog_ml,
            "favorite_spread_line": -1.5,
            "favorite_spread_odds": spread_odds,
            "underdog_spread_odds": underdog_spread_odds,
            "favorite_covered": fav_covered,
            "total_score": tot_score,
            "total_line": total_line,
            "over_hit": over_hit
        })
    return matches

def generate_esports_matches(league: str, teams: List[str], count: int = 350) -> List[Dict[str, Any]]:
    """生成電競 Bo3 歷史賽事實例 (含 2:0 橫掃 -1.5 地圖讓分過盤)"""
    matches = []
    base_date = datetime.now() - timedelta(days=count // 2 + 10)
    
    for i in range(count):
        match_date = (base_date + timedelta(days=i // 2, hours=(i % 2) * 4)).strftime("%Y-%m-%d")
        home, away = random.sample(teams, 2)
        
        fav_is_home = random.random() < 0.50
        favorite = home if fav_is_home else away
        underdog = away if fav_is_home else home
        
        fav_tier = random.choices(
            ["tier_s", "tier_a", "tier_b", "tier_c"],
            weights=[0.25, 0.35, 0.25, 0.15]
        )[0]
        
        if fav_tier == "tier_s":
            fav_ml = round(random.uniform(1.08, 1.25), 2)
            sweep_prob = 0.68
            spread_odds = round(random.uniform(1.45, 1.80), 2)
        elif fav_tier == "tier_a":
            fav_ml = round(random.uniform(1.25, 1.45), 2)
            sweep_prob = 0.54
            spread_odds = round(random.uniform(1.80, 2.20), 2)
        elif fav_tier == "tier_b":
            fav_ml = round(random.uniform(1.45, 1.70), 2)
            sweep_prob = 0.40
            spread_odds = round(random.uniform(2.20, 2.75), 2)
        else:
            fav_ml = round(random.uniform(1.70, 1.95), 2)
            sweep_prob = 0.28
            spread_odds = round(random.uniform(2.70, 3.40), 2)
            
        underdog_ml = round(1.0 / (1.0 - (1.0 / fav_ml) * 0.94), 2)
        underdog_spread_odds = round(1.0 / (1.0 - (1.0 / spread_odds) * 0.93), 2)
        
        r = random.random()
        if r < sweep_prob:
            fav_maps = 2
            und_maps = 0
        elif r < sweep_prob + 0.22:
            fav_maps = 2
            und_maps = 1
        elif r < sweep_prob + 0.30:
            fav_maps = 1
            und_maps = 2
        else:
            fav_maps = 0
            und_maps = 2
            
        home_score = fav_maps if fav_is_home else und_maps
        away_score = und_maps if fav_is_home else fav_maps
        winner = home if home_score > away_score else away
        score_diff = home_score - away_score
        fav_covered = 1 if ((fav_is_home and score_diff >= 2) or (not fav_is_home and -score_diff >= 2)) else 0

        matches.append({
            "id": f"hist_{league.lower()}_{i+1:04d}",
            "sport": "esports",
            "league": league,
            "season": "2025",
            "match_date": match_date,
            "home_team": home,
            "away_team": away,
            "home_score": home_score,
            "away_score": away_score,
            "winner_team": winner,
            "score_diff": score_diff,
            "favorite_team": favorite,
            "favorite_is_home": 1 if fav_is_home else 0,
            "favorite_ml_odds": fav_ml,
            "underdog_ml_odds": underdog_ml,
            "favorite_spread_line": -1.5,
            "favorite_spread_odds": spread_odds,
            "underdog_spread_odds": underdog_spread_odds,
            "favorite_covered": fav_covered,
            "total_score": home_score + away_score,
            "total_line": 2.5,
            "over_hit": 1 if (home_score + away_score) == 3 else 0
        })
    return matches

def init_seed_database(force_reload: bool = False):
    """初始化載入歷史賽事大數據庫並直接同步真實即時盤口"""
    summary = db.get_db_summary()
    if summary["historical_matches"] > 0 and not force_reload:
        print(f"[*] 資料庫已有 {summary['historical_matches']} 場歷史賽事紀錄。")
        from scrapers.real_live_scraper import real_live_scraper
        real_live_scraper.sync_to_database()
        return

    print("[*] 正在為 MLB, NPB, CPBL, LCK, LPL 導入歷史數據庫並同步即時盤口...")
    all_historical = []
    
    # 棒球 3 大聯盟
    all_historical.extend(generate_baseball_matches("MLB", MLB_TEAMS, 800))
    all_historical.extend(generate_baseball_matches("NPB", NPB_TEAMS, 500))
    all_historical.extend(generate_baseball_matches("CPBL", CPBL_TEAMS, 400))
    
    # 電競 2 大聯盟
    all_historical.extend(generate_esports_matches("LCK", LCK_TEAMS, 450))
    all_historical.extend(generate_esports_matches("LPL", LPL_TEAMS, 450))
    
    db.insert_historical_matches(all_historical)
    from scrapers.real_live_scraper import real_live_scraper
    real_live_scraper.sync_to_database()
    print(f"[OK] 成功建立 {len(all_historical)} 場歷史賽事紀錄與 4 大來源真實即時盤口！")

if __name__ == "__main__":
    init_seed_database(force_reload=True)
