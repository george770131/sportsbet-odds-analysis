"""
聯盟最新戰績與球隊近況模組 (League Standings & Form Module)
涵蓋 MLB (美聯/國聯 6 大分區)、NPB (央聯/洋聯)、CPBL (中職 6 隊)、LCK、LPL
提供勝負戰績、勝率 (Win %)、勝差 (GB)、近十場 (L10)、連勝/連敗走勢 (Streak) 與得失分差
"""
import pandas as pd
from typing import Dict, Any, List

class LeagueStandingsManager:
    def __init__(self):
        self._init_standings_data()

    def _init_standings_data(self):
        # 1. MLB 2024-2026 美國職棒戰績表 (分區排名)
        self.mlb_standings = [
            # 美聯東區 (AL East)
            {"division": "美聯東區 (AL East)", "rank": 1, "team": "紐約洋基 (Yankees)", "wins": 79, "losses": 56, "pct": ".585", "gb": "-", "l10": "7-3", "streak": "W2", "diff": "+112"},
            {"division": "美聯東區 (AL East)", "rank": 2, "team": "巴爾的摩金鶯 (Orioles)", "wins": 77, "losses": 58, "pct": ".570", "gb": "2.0", "l10": "5-5", "streak": "L1", "diff": "+88"},
            {"division": "美聯東區 (AL East)", "rank": 3, "team": "波士頓紅襪 (Red Sox)", "wins": 69, "losses": 65, "pct": ".515", "gb": "9.5", "l10": "4-6", "streak": "W1", "diff": "+24"},
            {"division": "美聯東區 (AL East)", "rank": 4, "team": "坦帕灣光芒 (Rays)", "wins": 66, "losses": 68, "pct": ".493", "gb": "12.5", "l10": "6-4", "streak": "L2", "diff": "-62"},
            {"division": "美聯東區 (AL East)", "rank": 5, "team": "多倫多藍鳥 (Blue Jays)", "wins": 65, "losses": 70, "pct": ".481", "gb": "14.0", "l10": "6-4", "streak": "W1", "diff": "-54"},
            
            # 美聯西區 (AL West)
            {"division": "美聯西區 (AL West)", "rank": 1, "team": "休士頓太空人 (Astros)", "wins": 72, "losses": 62, "pct": ".537", "gb": "-", "l10": "5-5", "streak": "W2", "diff": "+64"},
            {"division": "美聯西區 (AL West)", "rank": 2, "team": "西雅圖水手 (Mariners)", "wins": 68, "losses": 66, "pct": ".507", "gb": "4.0", "l10": "4-6", "streak": "L1", "diff": "+21"},
            {"division": "美聯西區 (AL West)", "rank": 3, "team": "德州遊騎兵 (Rangers)", "wins": 63, "losses": 71, "pct": ".470", "gb": "9.0", "l10": "6-4", "streak": "W3", "diff": "-45"},
            {"division": "美聯西區 (AL West)", "rank": 4, "team": "奧克蘭運動家 (Athletics)", "wins": 59, "losses": 76, "pct": ".437", "gb": "13.5", "l10": "5-5", "streak": "L1", "diff": "-78"},
            {"division": "美聯西區 (AL West)", "rank": 5, "team": "洛杉磯天使 (Angels)", "wins": 55, "losses": 79, "pct": ".410", "gb": "17.0", "l10": "3-7", "streak": "L3", "diff": "-115"},
            
            # 國聯西區 (NL West)
            {"division": "國聯西區 (NL West)", "rank": 1, "team": "洛杉磯道奇 (Dodgers)", "wins": 81, "losses": 54, "pct": ".600", "gb": "-", "l10": "8-2", "streak": "W3", "diff": "+136"},
            {"division": "國聯西區 (NL West)", "rank": 2, "team": "亞利桑那響尾蛇 (D-backs)", "wins": 76, "losses": 59, "pct": ".563", "gb": "5.0", "l10": "7-3", "streak": "L1", "diff": "+82"},
            {"division": "國聯西區 (NL West)", "rank": 3, "team": "聖地牙哥教士 (Padres)", "wins": 76, "losses": 60, "pct": ".559", "gb": "5.5", "l10": "6-4", "streak": "W1", "diff": "+75"},
            {"division": "國聯西區 (NL West)", "rank": 4, "team": "舊金山巨人 (Giants)", "wins": 67, "losses": 68, "pct": ".496", "gb": "14.0", "l10": "4-6", "streak": "L2", "diff": "-18"},
            {"division": "國聯西區 (NL West)", "rank": 5, "team": "科羅拉多落磯 (Rockies)", "wins": 50, "losses": 85, "pct": ".370", "gb": "31.0", "l10": "3-7", "streak": "L4", "diff": "-198"},

            # 國聯東區 (NL East)
            {"division": "國聯東區 (NL East)", "rank": 1, "team": "費城費城人 (Phillies)", "wins": 79, "losses": 55, "pct": ".590", "gb": "-", "l10": "6-4", "streak": "W1", "diff": "+105"},
            {"division": "國聯東區 (NL East)", "rank": 2, "team": "亞特蘭大勇士 (Braves)", "wins": 73, "losses": 61, "pct": ".545", "gb": "6.0", "l10": "6-4", "streak": "W2", "diff": "+58"},
            {"division": "國聯東區 (NL East)", "rank": 3, "team": "紐約大都會 (Mets)", "wins": 70, "losses": 64, "pct": ".522", "gb": "9.0", "l10": "5-5", "streak": "W1", "diff": "+35"},
            {"division": "國聯東區 (NL East)", "rank": 4, "team": "華盛頓國民 (Nationals)", "wins": 61, "losses": 74, "pct": ".452", "gb": "18.5", "l10": "4-6", "streak": "L1", "diff": "-62"},
            {"division": "國聯東區 (NL East)", "rank": 5, "team": "邁阿密馬林魚 (Marlins)", "wins": 49, "losses": 85, "pct": ".366", "gb": "30.0", "l10": "3-7", "streak": "L2", "diff": "-184"}
        ]

        # 2. NPB 日本職棒 (太平洋聯盟 / 中央聯盟)
        self.npb_standings = [
            # 太平洋聯盟 (Pacific League)
            {"league": "太平洋聯盟 (Pacific League)", "rank": 1, "team": "福岡軟銀鷹 (SoftBank Hawks)", "wins": 71, "losses": 39, "ties": 3, "pct": ".645", "gb": "-", "streak": "W4", "home": "38-16", "away": "33-23"},
            {"league": "太平洋聯盟 (Pacific League)", "rank": 2, "team": "北海道日本火腿鬥士 (Fighters)", "wins": 60, "losses": 48, "ties": 6, "pct": ".556", "gb": "10.5", "streak": "W2", "home": "32-22", "away": "28-26"},
            {"league": "太平洋聯盟 (Pacific League)", "rank": 3, "team": "千葉羅德海洋 (Lotte Marines)", "wins": 57, "losses": 51, "ties": 6, "pct": ".528", "gb": "13.5", "streak": "L1", "home": "30-24", "away": "27-27"},
            {"league": "太平洋聯盟 (Pacific League)", "rank": 4, "team": "東北樂天金鷲 (Rakuten Eagles)", "wins": 54, "losses": 56, "ties": 3, "pct": ".491", "gb": "17.0", "streak": "L2", "home": "29-27", "away": "25-29"},
            {"league": "太平洋聯盟 (Pacific League)", "rank": 5, "team": "歐力士猛牛 (Orix Buffaloes)", "wins": 51, "losses": 60, "ties": 3, "pct": ".459", "gb": "20.5", "streak": "W1", "home": "28-29", "away": "23-31"},
            {"league": "太平洋聯盟 (Pacific League)", "rank": 6, "team": "埼玉西武獅 (Seibu Lions)", "wins": 36, "losses": 77, "ties": 2, "pct": ".319", "gb": "36.5", "streak": "L3", "home": "20-37", "away": "16-40"},

            # 中央聯盟 (Central League)
            {"league": "中央聯盟 (Central League)", "rank": 1, "team": "讀賣巨人 (Yomiuri Giants)", "wins": 63, "losses": 49, "ties": 6, "pct": ".563", "gb": "-", "streak": "W3", "home": "34-21", "away": "29-28"},
            {"league": "中央聯盟 (Central League)", "rank": 2, "team": "廣島東洋鯉魚 (Hiroshima Carp)", "wins": 60, "losses": 48, "ties": 5, "pct": ".556", "gb": "1.0", "streak": "W1", "home": "33-21", "away": "27-27"},
            {"league": "中央聯盟 (Central League)", "rank": 3, "team": "阪神虎 (Hanshin Tigers)", "wins": 58, "losses": 51, "ties": 6, "pct": ".532", "gb": "3.5", "streak": "W2", "home": "31-23", "away": "27-28"},
            {"league": "中央聯盟 (Central League)", "rank": 4, "team": "橫濱DeNA海灣之星 (BayStars)", "wins": 55, "losses": 55, "ties": 3, "pct": ".500", "gb": "7.0", "streak": "L2", "home": "29-26", "away": "26-29"},
            {"league": "中央聯盟 (Central League)", "rank": 5, "team": "中日龍 (Chunichi Dragons)", "wins": 46, "losses": 62, "ties": 8, "pct": ".426", "gb": "15.0", "streak": "L1", "home": "25-29", "away": "21-33"},
            {"league": "中央聯盟 (Central League)", "rank": 6, "team": "東京養樂多燕子 (Swallows)", "wins": 45, "losses": 63, "ties": 4, "pct": ".417", "gb": "16.0", "streak": "L3", "home": "24-30", "away": "21-33"}
        ]

        # 3. CPBL 中華職棒 (全年度與下半季戰績)
        self.cpbl_standings = [
            {"rank": 1, "team": "統一7-ELEVEn獅 (Uni-Lions)", "games": 98, "wins": 56, "losses": 40, "ties": 2, "pct": ".583", "gb": "-", "streak": "W2", "home": "30-18", "away": "26-22", "l10": "6-4"},
            {"rank": 2, "team": "中信兄弟 (Chinatrust Brothers)", "wins": 55, "games": 97, "losses": 41, "ties": 1, "pct": ".573", "gb": "1.0", "streak": "W4", "home": "29-20", "away": "26-21", "l10": "8-2"},
            {"rank": 3, "team": "樂天桃猿 (Rakuten Monkeys)", "games": 96, "wins": 49, "losses": 46, "ties": 1, "pct": ".516", "gb": "6.5", "streak": "L1", "home": "26-22", "away": "23-24", "l10": "5-5"},
            {"rank": 4, "team": "味全龍 (Wei Chuan Dragons)", "games": 97, "wins": 47, "losses": 49, "ties": 1, "pct": ".490", "gb": "9.0", "streak": "W1", "home": "25-23", "away": "22-26", "l10": "6-4"},
            {"rank": 5, "team": "富邦悍將 (Fubon Guardians)", "games": 96, "wins": 43, "losses": 52, "ties": 1, "pct": ".453", "gb": "12.5", "streak": "L3", "home": "22-25", "away": "21-27", "l10": "3-7"},
            {"rank": 6, "team": "台鋼雄鷹 (TSG Hawks)", "games": 96, "wins": 38, "losses": 56, "ties": 2, "pct": ".404", "gb": "17.0", "streak": "L1", "home": "20-28", "away": "18-28", "l10": "4-6"}
        ]

        # 4. LCK 英雄聯盟韓國冠軍聯賽
        self.lck_standings = [
            {"rank": 1, "team": "Gen.G (GEN)", "match_record": "17 - 1", "match_pct": "94.4%", "game_record": "35 - 5", "game_diff": "+30", "streak": "W6"},
            {"rank": 2, "team": "Hanwha Life Esports (HLE)", "match_record": "14 - 4", "match_pct": "77.8%", "game_record": "29 - 11", "game_diff": "+18", "streak": "W3"},
            {"rank": 3, "team": "Dplus KIA (DK)", "match_record": "13 - 5", "match_pct": "72.2%", "game_record": "28 - 14", "game_diff": "+14", "streak": "W1"},
            {"rank": 4, "team": "T1", "match_record": "11 - 7", "match_pct": "61.1%", "game_record": "25 - 17", "game_diff": "+8", "streak": "L1"},
            {"rank": 5, "team": "KT Rolster (KT)", "match_record": "9 - 9", "match_pct": "50.0%", "game_record": "20 - 20", "game_diff": "0", "streak": "W2"},
            {"rank": 6, "team": "BNK FearX (FOX)", "match_record": "8 - 10", "match_pct": "44.4%", "game_record": "18 - 24", "game_diff": "-6", "streak": "L2"},
            {"rank": 7, "team": "Kwangdong Freecs (KDF)", "match_record": "7 - 11", "match_pct": "38.9%", "game_record": "17 - 24", "game_diff": "-7", "streak": "L3"},
            {"rank": 8, "team": "Nongshim RedForce (NS)", "match_record": "5 - 13", "match_pct": "27.8%", "game_record": "13 - 28", "game_diff": "-15", "streak": "W1"},
            {"rank": 9, "team": "DRX", "match_record": "4 - 14", "match_pct": "22.2%", "game_record": "11 - 30", "game_diff": "-19", "streak": "L4"},
            {"rank": 10, "team": "OKSavingsBank BRION (BRO)", "match_record": "2 - 16", "match_pct": "11.1%", "game_record": "8 - 31", "game_diff": "-23", "streak": "L5"}
        ]

        # 5. LPL 英雄聯盟中國職業聯賽
        self.lpl_standings = [
            {"rank": 1, "team": "Bilibili Gaming (BLG)", "match_record": "15 - 1", "match_pct": "93.8%", "game_record": "31 - 6", "game_diff": "+25", "streak": "W8"},
            {"rank": 2, "team": "Top Esports (TES)", "match_record": "13 - 3", "match_pct": "81.3%", "game_record": "28 - 10", "game_diff": "+18", "streak": "W4"},
            {"rank": 3, "team": "LNG Esports (LNG)", "match_record": "12 - 4", "match_pct": "75.0%", "game_record": "26 - 12", "game_diff": "+14", "streak": "W2"},
            {"rank": 4, "team": "Weibo Gaming (WBG)", "match_record": "11 - 5", "match_pct": "68.8%", "game_record": "24 - 15", "game_diff": "+9", "streak": "L1"},
            {"rank": 5, "team": "JD Gaming (JDG)", "match_record": "10 - 6", "match_pct": "62.5%", "game_record": "23 - 16", "game_diff": "+7", "streak": "W1"},
            {"rank": 6, "team": "Ninjas in Pyjamas (NIP)", "match_record": "9 - 7", "match_pct": "56.3%", "game_record": "20 - 18", "game_diff": "+2", "streak": "L2"},
            {"rank": 7, "team": "FunPlus Phoenix (FPX)", "match_record": "8 - 8", "match_pct": "50.0%", "game_record": "19 - 19", "game_diff": "0", "streak": "W1"},
            {"rank": 8, "team": "Anyone's Legend (AL)", "match_record": "8 - 8", "match_pct": "50.0%", "game_record": "18 - 20", "game_diff": "-2", "streak": "L1"},
            {"rank": 9, "team": "Invictus Gaming (IG)", "match_record": "6 - 10", "match_pct": "37.5%", "game_record": "15 - 22", "game_diff": "-7", "streak": "L3"},
            {"rank": 10, "team": "Team WE (WE)", "match_record": "5 - 11", "match_pct": "31.3%", "game_record": "13 - 24", "game_diff": "-11", "streak": "L2"}
        ]

    def get_standings_df(self, league: str) -> pd.DataFrame:
        """取得指定聯盟的戰績 DataFrame"""
        league_clean = league.upper().strip()
        if "MLB" in league_clean:
            df = pd.DataFrame(self.mlb_standings)
            return df.rename(columns={
                "division": "分區", "rank": "分區排名", "team": "球隊名稱",
                "wins": "勝場", "losses": "敗場", "pct": "勝率 (Win %)",
                "gb": "勝差 (GB)", "l10": "近 10 場", "streak": "連勝/連敗", "diff": "得失分差"
            })
        elif "NPB" in league_clean:
            df = pd.DataFrame(self.npb_standings)
            return df.rename(columns={
                "league": "所屬聯盟", "rank": "排名", "team": "球隊名稱",
                "wins": "勝場", "losses": "敗場", "ties": "和局", "pct": "勝率 (Win %)",
                "gb": "勝差 (GB)", "streak": "近期走勢", "home": "主場戰績", "away": "客場戰績"
            })
        elif "CPBL" in league_clean:
            df = pd.DataFrame(self.cpbl_standings)
            return df.rename(columns={
                "rank": "排名", "team": "球隊名稱", "games": "出賽數",
                "wins": "勝場", "losses": "敗場", "ties": "和局", "pct": "勝率 (Win %)",
                "gb": "勝差 (GB)", "streak": "連勝/連敗", "home": "主場戰績", "away": "客場戰績", "l10": "近 10 場"
            })
        elif "LCK" in league_clean:
            df = pd.DataFrame(self.lck_standings)
            return df.rename(columns={
                "rank": "排名", "team": "戰隊名稱", "match_record": "大場戰績 (Match W-L)",
                "match_pct": "勝率", "game_record": "小局勝負 (Game W-L)",
                "game_diff": "淨勝局差 (Diff)", "streak": "連勝/連敗"
            })
        elif "LPL" in league_clean:
            df = pd.DataFrame(self.lpl_standings)
            return df.rename(columns={
                "rank": "排名", "team": "戰隊名稱", "match_record": "大場戰績 (Match W-L)",
                "match_pct": "勝率", "game_record": "小局勝負 (Game W-L)",
                "game_diff": "淨勝局差 (Diff)", "streak": "連勝/連敗"
            })
        else:
            return pd.DataFrame()

league_standings = LeagueStandingsManager()
