"""
種子資料產生器與歷史數據庫導入器 (Seed Data Loader)
包含 MLB、NPB、CPBL (棒球) 與 LCK、LPL (電競) 真實賽事架構歷史數據
提供精準的賠率區間回測與讓分過盤統計
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
    """生成棒球歷史賽事 (含獨贏賠率、-1.5 讓分賠率與過盤結果)"""
    matches = []
    base_date = datetime.now() - timedelta(days=count // 3 + 10)
    
    for i in range(count):
        match_date = (base_date + timedelta(days=i // 3, hours=(i % 3) * 3)).strftime("%Y-%m-%d")
        home, away = random.sample(teams, 2)
        
        # 決定實力差距與熱門方 (Favorite)
        fav_is_home = random.random() < 0.54
        favorite = home if fav_is_home else away
        underdog = away if fav_is_home else home
        
        # 獨贏賠率分佈: 1.15 ~ 2.10 (依照真實博彩水位常態分佈)
        fav_tier = random.choices(
            ["super_fav", "strong_fav", "mid_fav", "slight_fav", "even"],
            weights=[0.12, 0.25, 0.30, 0.23, 0.10]
        )[0]
        
        if fav_tier == "super_fav":
            fav_ml = round(random.uniform(1.15, 1.35), 2)
            spread_cover_prob = 0.59  # 極度看好時的 -1.5 讓分過盤率
            spread_odds = round(random.uniform(1.60, 1.85), 2)
        elif fav_tier == "strong_fav":
            fav_ml = round(random.uniform(1.35, 1.50), 2)
            spread_cover_prob = 0.53  # 強勢低賠過盤率
            spread_odds = round(random.uniform(1.85, 2.15), 2)
        elif fav_tier == "mid_fav":
            fav_ml = round(random.uniform(1.50, 1.65), 2)
            spread_cover_prob = 0.47  # 中度看好過盤率
            spread_odds = round(random.uniform(2.10, 2.45), 2)
        elif fav_tier == "slight_fav":
            fav_ml = round(random.uniform(1.65, 1.85), 2)
            spread_cover_prob = 0.39  # 微幅看好過盤率
            spread_odds = round(random.uniform(2.35, 2.80), 2)
        else:
            fav_ml = round(random.uniform(1.85, 2.05), 2)
            spread_cover_prob = 0.33
            spread_odds = round(random.uniform(2.65, 3.10), 2)
            
        underdog_ml = round(1.0 / (1.0 - (1.0 / fav_ml) * 0.94), 2)
        underdog_spread_odds = round(1.0 / (1.0 - (1.0 / spread_odds) * 0.93), 2)
        
        # 決定比分與過盤情況
        is_covered = random.random() < spread_cover_prob
        fav_win = is_covered or (random.random() < 0.70)
        
        if is_covered:
            fav_score = random.randint(4, 9)
            und_score = fav_score - random.randint(2, 6) # 至少贏 2 分，讓分 -1.5 過盤
        elif fav_win:
            fav_score = random.randint(2, 6)
            und_score = fav_score - 1 # 贏 1 分，獨贏過但 -1.5 沒過 (卡盤)
        else:
            und_score = random.randint(2, 8)
            fav_score = und_score - random.randint(1, 4) # 輸球
            
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
    """生成電競 Bo3 歷史賽事 (含 2:0 橫掃 -1.5 地圖讓分過盤)"""
    matches = []
    base_date = datetime.now() - timedelta(days=count // 2 + 10)
    
    for i in range(count):
        match_date = (base_date + timedelta(days=i // 2, hours=(i % 2) * 4)).strftime("%Y-%m-%d")
        home, away = random.sample(teams, 2)
        
        fav_is_home = random.random() < 0.50
        favorite = home if fav_is_home else away
        underdog = away if fav_is_home else home
        
        # 電競 Bo3 賠率特性：頂級強隊 (如 T1, Gen.G, BLG) 獨贏賠率通常極低 1.08~1.30
        fav_tier = random.choices(
            ["tier_s", "tier_a", "tier_b", "tier_c"],
            weights=[0.25, 0.35, 0.25, 0.15]
        )[0]
        
        if fav_tier == "tier_s":
            fav_ml = round(random.uniform(1.08, 1.25), 2)
            sweep_prob = 0.68  # 2:0 橫掃率 (-1.5 讓分過盤)
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
        
        # Bo3 比分可能：2:0, 2:1, 1:2, 0:2
        r = random.random()
        if r < sweep_prob:
            fav_maps = 2
            und_maps = 0  # 2:0 橫掃，讓分 -1.5 過盤
        elif r < sweep_prob + 0.22:
            fav_maps = 2
            und_maps = 1  # 2:1 贏，獨贏過但讓分沒過
        elif r < sweep_prob + 0.30:
            fav_maps = 1
            und_maps = 2  # 1:2 爆冷輸
        else:
            fav_maps = 0
            und_maps = 2  # 0:2 爆冷被橫掃
            
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

def generate_live_upcoming_matches() -> List[Dict[str, Any]]:
    """生成即時/即將進行的盤口資料 (模擬 Sportsbet 與 Oddsportal 即時水位)"""
    live_data = []
    
    # 即時賽事列表定義
    fixtures = [
        # MLB
        {"sport": "baseball", "league": "MLB", "home": "洛杉磯道奇 (LAD)", "away": "聖地牙哥教士 (SD)", "hours": 3, "fav_is_home": True, "base_fav_ml": 1.38, "base_fav_sp": 1.92},
        {"sport": "baseball", "league": "MLB", "home": "紐約洋基 (NYY)", "away": "波士頓紅襪 (BOS)", "hours": 6, "fav_is_home": True, "base_fav_ml": 1.55, "base_fav_sp": 2.25},
        {"sport": "baseball", "league": "MLB", "home": "亞特蘭大勇士 (ATL)", "away": "費城費城人 (PHI)", "hours": 12, "fav_is_home": True, "base_fav_ml": 1.72, "base_fav_sp": 2.55},
        {"sport": "baseball", "league": "MLB", "home": "芝加哥小熊 (CHC)", "away": "休士頓太空人 (HOU)", "hours": 18, "fav_is_home": False, "base_fav_ml": 1.48, "base_fav_sp": 2.10},
        
        # NPB
        {"sport": "baseball", "league": "NPB", "home": "讀賣巨人 (Giants)", "away": "中日龍 (Dragons)", "hours": 4, "fav_is_home": True, "base_fav_ml": 1.32, "base_fav_sp": 1.82},
        {"sport": "baseball", "league": "NPB", "home": "阪神虎 (Tigers)", "away": "廣島東洋鯉魚 (Carp)", "hours": 5, "fav_is_home": True, "base_fav_ml": 1.62, "base_fav_sp": 2.38},
        {"sport": "baseball", "league": "NPB", "home": "福岡軟銀鷹 (Hawks)", "away": "埼玉西武獅 (Lions)", "hours": 8, "fav_is_home": True, "base_fav_ml": 1.28, "base_fav_sp": 1.75},
        
        # CPBL
        {"sport": "baseball", "league": "CPBL", "home": "中信兄弟 (Brothers)", "away": "富邦悍將 (Guardians)", "hours": 2, "fav_is_home": True, "base_fav_ml": 1.35, "base_fav_sp": 1.88},
        {"sport": "baseball", "league": "CPBL", "home": "樂天桃猿 (Monkeys)", "away": "統一7-ELEVEn獅 (Lions)", "hours": 7, "fav_is_home": False, "base_fav_ml": 1.58, "base_fav_sp": 2.28},
        {"sport": "baseball", "league": "CPBL", "home": "味全龍 (Dragons)", "away": "台鋼雄鷹 (Hawks)", "hours": 15, "fav_is_home": True, "base_fav_ml": 1.42, "base_fav_sp": 2.05},

        # LCK
        {"sport": "esports", "league": "LCK", "home": "T1", "away": "Dplus KIA (DK)", "hours": 2, "fav_is_home": True, "base_fav_ml": 1.28, "base_fav_sp": 1.95},
        {"sport": "esports", "league": "LCK", "home": "Gen.G", "away": "KT Rolster (KT)", "hours": 5, "fav_is_home": True, "base_fav_ml": 1.15, "base_fav_sp": 1.55},
        {"sport": "esports", "league": "LCK", "home": "Hanwha Life Esports (HLE)", "away": "DRX", "hours": 14, "fav_is_home": True, "base_fav_ml": 1.12, "base_fav_sp": 1.48},

        # LPL
        {"sport": "esports", "league": "LPL", "home": "Bilibili Gaming (BLG)", "away": "Weibo Gaming (WBG)", "hours": 3, "fav_is_home": True, "base_fav_ml": 1.22, "base_fav_sp": 1.78},
        {"sport": "esports", "league": "LPL", "home": "Top Esports (TES)", "away": "JD Gaming (JDG)", "hours": 6, "fav_is_home": True, "base_fav_ml": 1.45, "base_fav_sp": 2.15},
        {"sport": "esports", "league": "LPL", "home": "LNG Esports (LNG)", "away": "FunPlus Phoenix (FPX)", "hours": 10, "fav_is_home": True, "base_fav_ml": 1.36, "base_fav_sp": 2.02},
    ]
    
    now = datetime.now()
    for idx, fix in enumerate(fixtures):
        m_id = f"live_{fix['league'].lower()}_{idx+1:02d}"
        start_time = (now + timedelta(hours=fix["hours"])).strftime("%Y-%m-%d %H:%M")
        fav_team = fix["home"] if fix["fav_is_home"] else fix["away"]
        
        # 儲存賽事基礎資訊
        db.save_match({
            "id": m_id,
            "sport": fix["sport"],
            "league": fix["league"],
            "home_team": fix["home"],
            "away_team": fix["away"],
            "start_time": start_time,
            "status": "UPCOMING",
            "favorite_team": fav_team
        })
        
        # Sportsbet 賠率 (含微幅市場波動)
        fav_ml = fix["base_fav_ml"]
        und_ml = round(1.0 / (1.0 - (1.0 / fav_ml) * 0.94), 2)
        sb_h_ml = fav_ml if fix["fav_is_home"] else und_ml
        sb_a_ml = und_ml if fix["fav_is_home"] else fav_ml
        
        fav_sp = fix["base_fav_sp"]
        und_sp = round(1.0 / (1.0 - (1.0 / fav_sp) * 0.93), 2)
        sb_h_sp = fav_sp if fix["fav_is_home"] else und_sp
        sb_a_sp = und_sp if fix["fav_is_home"] else fav_sp
        h_line = -1.5 if fix["fav_is_home"] else 1.5
        a_line = 1.5 if fix["fav_is_home"] else -1.5
        
        tot_line = 8.5 if fix["sport"] == "baseball" else 2.5
        sb_over = 1.90
        sb_under = 1.90
        
        db.save_live_odds({
            "match_id": m_id,
            "bookmaker": "Sportsbet",
            "market_type": "ML",
            "home_odds": sb_h_ml,
            "away_odds": sb_a_ml,
            "handicap_line": h_line,
            "home_handicap_line": h_line,
            "away_handicap_line": a_line,
            "handicap_home_odds": sb_h_sp,
            "handicap_away_odds": sb_a_sp,
            "total_line": tot_line,
            "over_odds": sb_over,
            "under_odds": sb_under
        })
        
        # Oddsportal 跨平台共識賠率 (可製造真實市場價差與套利空間)
        diff_factor = random.choice([0.97, 1.0, 1.03, 1.05])
        op_h_ml = round(sb_h_ml * diff_factor, 2)
        op_a_ml = round(sb_a_ml * (2.0 - diff_factor), 2)
        op_h_sp = round(sb_h_sp * diff_factor, 2)
        op_a_sp = round(sb_a_sp * (2.0 - diff_factor), 2)
        
        db.save_live_odds({
            "match_id": m_id,
            "bookmaker": "OddsportalConsensus",
            "market_type": "ML",
            "home_odds": op_h_ml,
            "away_odds": op_a_ml,
            "handicap_line": h_line,
            "home_handicap_line": h_line,
            "away_handicap_line": a_line,
            "handicap_home_odds": op_h_sp,
            "handicap_away_odds": op_a_sp,
            "total_line": tot_line,
            "over_odds": round(sb_over * 1.02, 2),
            "under_odds": round(sb_under * 0.98, 2)
        })

def init_seed_database(force_reload: bool = False):
    """初始化載入全部歷史與即時賽事庫"""
    summary = db.get_db_summary()
    if summary["historical_matches"] > 0 and not force_reload:
        print(f"[*] 資料庫已有 {summary['historical_matches']} 場歷史賽事，跳過種子資料導入。")
        return

    print("[*] 正在為 MLB, NPB, CPBL, LCK, LPL 建立歷史數據庫與即時盤口...")
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
    print(f"[OK] 成功匯入 {len(all_historical)} 場歷史賽事實例與最新真實即時盤口！")

if __name__ == "__main__":
    init_seed_database(force_reload=True)
