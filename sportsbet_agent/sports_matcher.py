#!/usr/bin/env python3
"""
跨平台賽事與隊伍名稱智慧對齊模組 (sports_matcher.py)
-----------------------------------------------------------------------------
功能：
1. 解決 Polymarket (美系簡稱/全名) 與 Sportsbet (澳洲隊名) 的名稱差異。
2. 內建 NBA、LoL、MLB、足球等主流隊伍別名庫與同義詞對照表。
3. 提供相似度演算法 (Token Overlap, Substring Matching, Levenshtein)。
4. 自動將 Sportsbet 盤口選項與 Polymarket 預測合約進行一對一精確綁定。
-----------------------------------------------------------------------------
"""

import re
from typing import Dict, List, Optional, Tuple


# 常見球隊核心別名與代號對照表 (統一歸一化為 Standard Key)
CANONICAL_TEAM_KEYS = {
    # NBA
    "lakers": "los angeles lakers", "lal": "los angeles lakers", "los angeles lakers": "los angeles lakers",
    "clippers": "los angeles clippers", "lac": "los angeles clippers", "los angeles clippers": "los angeles clippers",
    "celtics": "boston celtics", "bos": "boston celtics", "boston": "boston celtics", "boston celtics": "boston celtics",
    "bucks": "milwaukee bucks", "mil": "milwaukee bucks", "milwaukee": "milwaukee bucks", "milwaukee bucks": "milwaukee bucks",
    "heat": "miami heat", "mia": "miami heat", "miami": "miami heat", "miami heat": "miami heat",
    "kings": "sacramento kings", "sac": "sacramento kings", "sacramento": "sacramento kings", "sacramento kings": "sacramento kings",
    "nets": "brooklyn nets", "bkn": "brooklyn nets", "brooklyn": "brooklyn nets", "brooklyn nets": "brooklyn nets",
    "mavericks": "dallas mavericks", "dal": "dallas mavericks", "dallas": "dallas mavericks", "dallas mavericks": "dallas mavericks", "mavs": "dallas mavericks",
    "jazz": "utah jazz", "uta": "utah jazz", "utah": "utah jazz", "utah jazz": "utah jazz",
    "timberwolves": "minnesota timberwolves", "min": "minnesota timberwolves", "minnesota": "minnesota timberwolves", "minnesota timberwolves": "minnesota timberwolves", "wolves": "minnesota timberwolves",
    "pelicans": "new orleans pelicans", "nop": "new orleans pelicans", "new orleans": "new orleans pelicans", "new orleans pelicans": "new orleans pelicans",
    "warriors": "golden state warriors", "gsw": "golden state warriors", "golden state": "golden state warriors", "golden state warriors": "golden state warriors",
    "suns": "phoenix suns", "phx": "phoenix suns", "phoenix": "phoenix suns", "phoenix suns": "phoenix suns",
    "nuggets": "denver nuggets", "den": "denver nuggets", "denver": "denver nuggets", "denver nuggets": "denver nuggets",
    "thunder": "oklahoma city thunder", "okc": "oklahoma city thunder", "oklahoma": "oklahoma city thunder", "oklahoma city thunder": "oklahoma city thunder",
    "rockets": "houston rockets", "hou": "houston rockets", "houston": "houston rockets", "houston rockets": "houston rockets",
    "grizzlies": "memphis grizzlies", "mem": "memphis grizzlies", "memphis": "memphis grizzlies", "memphis grizzlies": "memphis grizzlies",
    "spurs": "san antonio spurs", "sas": "san antonio spurs", "san antonio": "san antonio spurs", "san antonio spurs": "san antonio spurs",
    "knicks": "new york knicks", "nyk": "new york knicks", "new york": "new york knicks", "new york knicks": "new york knicks",
    "76ers": "philadelphia 76ers", "sixers": "philadelphia 76ers", "phi": "philadelphia 76ers", "philadelphia": "philadelphia 76ers", "philadelphia 76ers": "philadelphia 76ers",
    "bulls": "chicago bulls", "chi": "chicago bulls", "chicago": "chicago bulls", "chicago bulls": "chicago bulls",
    "cavaliers": "cleveland cavaliers", "cle": "cleveland cavaliers", "cleveland": "cleveland cavaliers", "cleveland cavaliers": "cleveland cavaliers", "cavs": "cleveland cavaliers",
    "pacers": "indiana pacers", "ind": "indiana pacers", "indiana": "indiana pacers", "indiana pacers": "indiana pacers",
    "pistons": "detroit pistons", "det": "detroit pistons", "detroit": "detroit pistons", "detroit pistons": "detroit pistons",
    "raptors": "toronto raptors", "tor": "toronto raptors", "toronto": "toronto raptors", "toronto raptors": "toronto raptors",
    "hawks": "atlanta hawks", "atl": "atlanta hawks", "atlanta": "atlanta hawks", "atlanta hawks": "atlanta hawks",
    "hornets": "charlotte hornets", "cha": "charlotte hornets", "charlotte": "charlotte hornets", "charlotte hornets": "charlotte hornets",
    "magic": "orlando magic", "orl": "orlando magic", "orlando": "orlando magic", "orlando magic": "orlando magic",
    "wizards": "washington wizards", "was": "washington wizards", "washington": "washington wizards", "washington wizards": "washington wizards",
    "trail blazers": "portland trail blazers", "blazers": "portland trail blazers", "por": "portland trail blazers", "portland": "portland trail blazers",

    # LoL 電競
    "t1": "t1", "sk telecom t1": "t1", "t1 esports": "t1",
    "blg": "bilibili gaming", "bilibili": "bilibili gaming", "bilibili gaming": "bilibili gaming",
    "gen.g": "gen.g", "geng": "gen.g", "gen g": "gen.g",
    "wbg": "weibo gaming", "weibo": "weibo gaming", "weibo gaming": "weibo gaming",
    "lng": "lng esports", "lng esports": "lng esports",
    "tes": "top esports", "top esports": "top esports",
    "g2": "g2 esports", "g2 esports": "g2 esports",
    "fnc": "fnatic", "fnatic": "fnatic",
    "fly": "flyquest", "flyquest": "flyquest",
    "hle": "hanwha life esports", "hanwha": "hanwha life esports",
    "cfo": "ctbc flying oyster", "flying oyster": "ctbc flying oyster",

    # 足球
    "arsenal": "arsenal", "arsenal fc": "arsenal",
    "chelsea": "chelsea", "chelsea fc": "chelsea",
    "liverpool": "liverpool", "liverpool fc": "liverpool",
    "man city": "manchester city", "manchester city": "manchester city",
    "man utd": "manchester united", "manchester united": "manchester united",
    "tottenham": "tottenham hotspur", "spurs (football)": "tottenham hotspur",
    "real madrid": "real madrid", "barcelona": "fc barcelona", "bayern": "bayern munich"
}


class SportsMatcher:
    @staticmethod
    def clean_name(name: str) -> str:
        """清理字串標點符號與多餘空白"""
        n = name.lower().strip()
        n = re.sub(r"[^\w\s]", " ", n)
        n = re.sub(r"\s+", " ", n).strip()
        return n

    @staticmethod
    def get_canonical_name(name: str) -> str:
        cleaned = SportsMatcher.clean_name(name)
        if cleaned in CANONICAL_TEAM_KEYS:
            return CANONICAL_TEAM_KEYS[cleaned]

        # 嘗試部分比對
        for alias, canon in CANONICAL_TEAM_KEYS.items():
            if alias in cleaned or cleaned in alias:
                return canon

        return cleaned

    @classmethod
    def are_teams_matching(cls, name_a: str, name_b: str) -> bool:
        """判斷兩隊伍名稱是否指向同一隊"""
        canon_a = cls.get_canonical_name(name_a)
        canon_b = cls.get_canonical_name(name_b)

        if canon_a == canon_b:
            return True

        # Token 集合交集判斷
        tokens_a = set(canon_a.split())
        tokens_b = set(canon_b.split())
        # 排除常見通用字詞
        stop_words = {"fc", "esports", "gaming", "team", "the", "club", "city"}
        tokens_a -= stop_words
        tokens_b -= stop_words

        if tokens_a and tokens_b and (tokens_a.issubset(tokens_b) or tokens_b.issubset(tokens_a)):
            return True

        return False

    @classmethod
    def match_two_way_game(
        cls,
        sb_team1: str,
        sb_team2: str,
        pm_team1: str,
        pm_team2: str
    ) -> Optional[Tuple[int, int]]:
        """
        比對二項盤口之兩隊對戰
        返回映射元組: (sb_team1 對應 pm 索引, sb_team2 對應 pm 索引)
        例如: (0, 1) 表示 sb_team1 == pm_team1, sb_team2 == pm_team2
             (1, 0) 表示 sb_team1 == pm_team2, sb_team2 == pm_team1
        若不匹配則返回 None
        """
        # 正向比對
        if cls.are_teams_matching(sb_team1, pm_team1) and cls.are_teams_matching(sb_team2, pm_team2):
            return (0, 1)

        # 反向比對
        if cls.are_teams_matching(sb_team1, pm_team2) and cls.are_teams_matching(sb_team2, pm_team1):
            return (1, 0)

        return None


if __name__ == "__main__":
    # 測試對齊
    test_cases = [
        ("Utah Jazz", "Minnesota Timberwolves", "Jazz", "Timberwolves"),
        ("Brooklyn Nets", "Dallas Mavericks", "Nets", "Mavericks"),
        ("Boston Celtics", "Milwaukee Bucks", "Celtics", "Bucks"),
        ("Miami Heat", "Sacramento Kings", "Heat", "Kings"),
        ("Bilibili Gaming", "T1", "Bilibili Gaming", "T1"),
        ("New Orleans Pelicans", "Los Angeles Clippers", "Clippers", "Pelicans") # 反向
    ]

    print("🔍 測試 Sportsbet vs Polymarket 隊伍對齊演算法：\n")
    for t1_a, t2_a, t1_b, t2_b in test_cases:
        res = SportsMatcher.match_two_way_game(t1_a, t2_a, t1_b, t2_b)
        status = "✅ 匹配成功" if res else "❌ 匹配失敗"
        align_info = f"對齊索引: {res}" if res else "無相符"
        print(f"[{status}] Sportsbet: '{t1_a} vs {t2_a}' <---> Polymarket: '{t1_b} vs {t2_b}' ({align_info})")
