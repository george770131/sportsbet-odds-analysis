"""
跨平台賽事與隊伍實體智慧對齊引擎 (radar/matcher.py)
支援繁體中文 (台灣運彩 / 玩運彩) ↔ 英文標準隊名 (Polymarket / Kalshi / Pinnacle / Betfair / Bet365 / Sportsbet)
覆蓋：NBA、MLB、NPB、CPBL、NHL、歐洲足球 (EPL / UCL / LaLiga / Bundesliga / Serie A)、LoL 電競
"""
import re
from typing import Dict, List, Optional, Tuple

# 1. 繁中簡稱 / 台灣運彩常用隊名 -> 英文標準 Canonical Key
ZH_TO_CANONICAL: Dict[str, str] = {
    # NBA (全部 30 隊)
    "老鷹": "atlanta hawks", "亞特蘭大老鷹": "atlanta hawks",
    "塞爾提": "boston celtics", "塞爾提克": "boston celtics", "賽爾提克": "boston celtics", "綠衫軍": "boston celtics",
    "籃網": "brooklyn nets", "布魯克林籃網": "brooklyn nets",
    "黃蜂": "charlotte hornets", "夏洛特黃蜂": "charlotte hornets",
    "公牛": "chicago bulls", "芝加哥公牛": "chicago bulls",
    "騎士": "cleveland cavaliers", "克里夫蘭騎士": "cleveland cavaliers",
    "獨行俠": "dallas mavericks", "達拉斯獨行俠": "dallas mavericks", "小牛": "dallas mavericks",
    "金塊": "denver nuggets", "丹佛金塊": "denver nuggets",
    "活塞": "detroit pistons", "底特律活塞": "detroit pistons",
    "勇士": "golden state warriors", "金州勇士": "golden state warriors",
    "火箭": "houston rockets", "休士頓火箭": "houston rockets",
    "溜馬": "indiana pacers", "印第安納溜馬": "indiana pacers",
    "快艇": "los angeles clippers", "洛杉磯快艇": "los angeles clippers",
    "湖人": "los angeles lakers", "洛杉磯湖人": "los angeles lakers",
    "灰熊": "memphis grizzlies", "曼菲斯灰熊": "memphis grizzlies",
    "熱火": "miami heat", "邁阿密熱火": "miami heat",
    "公鹿": "milwaukee bucks", "密爾瓦基公鹿": "milwaukee bucks",
    "灰狼": "minnesota timberwolves", "明尼蘇達灰狼": "minnesota timberwolves",
    "鵜鶘": "new orleans pelicans", "紐奧良鵜鶘": "new orleans pelicans",
    "尼克": "new york knicks", "紐約尼克": "new york knicks",
    "雷霆": "oklahoma city thunder", "奧克拉荷馬雷霆": "oklahoma city thunder",
    "魔術": "orlando magic", "奧蘭多魔術": "orlando magic",
    "76人": "philadelphia 76ers", "七六人": "philadelphia 76ers", "費城76人": "philadelphia 76ers",
    "太陽": "phoenix suns", "鳳凰城太陽": "phoenix suns",
    "拓荒者": "portland trail blazers", "波特蘭拓荒者": "portland trail blazers",
    "國王": "sacramento kings", "沙加緬度國王": "sacramento kings",
    "馬刺": "san antonio spurs", "聖安東尼奧馬刺": "san antonio spurs",
    "暴龍": "toronto raptors", "多倫多暴龍": "toronto raptors",
    "爵士": "utah jazz", "猶他爵士": "utah jazz",
    "巫師": "washington wizards", "華盛頓巫師": "washington wizards",

    # MLB (全部 30 隊)
    "響尾蛇": "arizona diamondbacks", "亞利桑那響尾蛇": "arizona diamondbacks",
    "勇士隊": "atlanta braves", "亞特蘭大勇士": "atlanta braves",
    "金鶯": "baltimore orioles", "巴爾的摩金鶯": "baltimore orioles",
    "紅襪": "boston red sox", "波士頓紅襪": "boston red sox",
    "小熊": "chicago cubs", "芝加哥小熊": "chicago cubs",
    "白襪": "chicago white sox", "芝加哥白襪": "chicago white sox",
    "紅人": "cincinnati reds", "辛辛那提紅人": "cincinnati reds",
    "守護者": "cleveland guardians", "克里夫蘭守護者": "cleveland guardians",
    "落磯": "colorado rockies", "科羅拉多落磯": "colorado rockies",
    "老虎": "detroit tigers", "底特律老虎": "detroit tigers",
    "太空人": "houston astros", "休士頓太空人": "houston astros",
    "皇家": "kansas city royals", "堪薩斯皇家": "kansas city royals",
    "天使": "los angeles angels", "洛杉磯天使": "los angeles angels",
    "道奇": "los angeles dodgers", "洛杉磯道奇": "los angeles dodgers",
    "馬林魚": "miami marlins", "邁阿密馬林魚": "miami marlins",
    "釀酒人": "milwaukee brewers", "密爾瓦基釀酒人": "milwaukee brewers",
    "雙城": "minnesota twins", "明尼蘇達雙城": "minnesota twins",
    "大都會": "new york mets", "紐約大都會": "new york mets",
    "洋基": "new york yankees", "紐約洋基": "new york yankees",
    "運動家": "athletics", "奧克蘭運動家": "athletics",
    "費城人": "philadelphia phillies", "費城費城人": "philadelphia phillies",
    "海盜": "pittsburgh pirates", "匹茲堡海盜": "pittsburgh pirates",
    "教士": "san diego padres", "聖地牙哥教士": "san diego padres",
    "巨人": "san francisco giants", "舊金山巨人": "san francisco giants",
    "水手": "seattle mariners", "西雅圖水手": "seattle mariners",
    "紅雀": "st louis cardinals", "聖路易紅雀": "st louis cardinals",
    "光芒": "tampa bay rays", "坦帕灣光芒": "tampa bay rays",
    "遊騎兵": "texas rangers", "德州遊騎兵": "texas rangers",
    "藍鳥": "toronto blue jays", "多倫多藍鳥": "toronto blue jays",
    "國民": "washington nationals", "華盛頓國民": "washington nationals",

    # CPBL (中華職棒 6 隊)
    "中信兄弟": "ctbc brothers", "兄弟": "ctbc brothers", "中信": "ctbc brothers",
    "統一獅": "uni president lions", "統一7-eleven獅": "uni president lions", "統一": "uni president lions",
    "樂天桃猿": "rakuten monkeys", "桃猿": "rakuten monkeys", "樂天": "rakuten monkeys",
    "味全龍": "wei chuan dragons", "味全": "wei chuan dragons",
    "富邦悍將": "fubon guardians", "富邦": "fubon guardians", "悍將": "fubon guardians",
    "台鋼雄鷹": "tsg hawks", "台鋼": "tsg hawks", "雄鷹": "tsg hawks",

    # NPB (日本職棒 12 隊)
    "讀賣巨人": "yomiuri giants", "養樂多": "tokyo yakult swallows", "養樂多燕子": "tokyo yakult swallows",
    "橫濱": "yokohama dena baystars", "橫濱海灣之星": "yokohama dena baystars",
    "阪神虎": "hanshin tigers", "阪神": "hanshin tigers",
    "廣島": "hiroshima toyo carp", "廣島鯉魚": "hiroshima toyo carp",
    "中日龍": "chunichi dragons", "中日": "chunichi dragons",
    "歐力士": "orix buffaloes", "軟體銀行": "fukuoka softbank hawks", "軟銀": "fukuoka softbank hawks", "軟銀鷹": "fukuoka softbank hawks",
    "羅德": "chiba lotte marines", "千葉羅德": "chiba lotte marines",
    "樂天金鷲": "tohoku rakuten golden eagles",
    "西武獅": "saitama seibu lions", "西武": "saitama seibu lions",
    "日本火腿": "hokkaido nippon ham fighters", "火腿": "hokkaido nippon ham fighters",

    # 歐洲五大足球主要隊伍
    "兵工廠": "arsenal", "阿森納": "arsenal",
    "切爾西": "chelsea", "利物浦": "liverpool",
    "曼城": "manchester city", "曼聯": "manchester united",
    "熱刺": "tottenham hotspur", "托特納姆熱刺": "tottenham hotspur",
    "紐卡索": "newcastle united", "維拉": "aston villa", "阿斯頓維拉": "aston villa",
    "皇馬": "real madrid", "皇家馬德里": "real madrid",
    "巴塞隆納": "fc barcelona", "巴薩": "fc barcelona",
    "馬德里競技": "atletico madrid", "馬競": "atletico madrid",
    "拜仁慕尼黑": "bayern munich", "拜仁": "bayern munich",
    "多特蒙德": "borussia dortmund", "多特": "borussia dortmund",
    "國際米蘭": "inter milan", "國米": "inter milan",
    "ac米蘭": "ac milan", "尤文圖斯": "juventus", "拿坡里": "napoli",
    "巴黎聖日耳曼": "paris saint germain", "大巴黎": "paris saint germain",

    # NHL 常見隊伍
    "油人": "edmonton oilers", "愛德蒙頓油人": "edmonton oilers",
    "美洲豹": "florida panthers", "楓葉": "toronto maple leafs",
    "遊騎兵(冰球)": "new york rangers", "雪崩": "colorado avalanche",
    "黃金騎士": "vegas golden knights", "棕熊": "boston bruins",
}

# 2. 英文縮寫 / 別名 -> Canonical Key
EN_TO_CANONICAL: Dict[str, str] = {
    # NBA
    "hawks": "atlanta hawks", "atl": "atlanta hawks", "atlanta": "atlanta hawks", "atlanta hawks": "atlanta hawks",
    "celtics": "boston celtics", "bos": "boston celtics", "boston": "boston celtics", "boston celtics": "boston celtics",
    "nets": "brooklyn nets", "bkn": "brooklyn nets", "brooklyn": "brooklyn nets", "brooklyn nets": "brooklyn nets",
    "hornets": "charlotte hornets", "cha": "charlotte hornets", "charlotte": "charlotte hornets", "charlotte hornets": "charlotte hornets",
    "bulls": "chicago bulls", "chi": "chicago bulls", "chicago bulls": "chicago bulls",
    "cavaliers": "cleveland cavaliers", "cavs": "cleveland cavaliers", "cle": "cleveland cavaliers", "cleveland cavaliers": "cleveland cavaliers",
    "mavericks": "dallas mavericks", "mavs": "dallas mavericks", "dal": "dallas mavericks", "dallas mavericks": "dallas mavericks",
    "nuggets": "denver nuggets", "den": "denver nuggets", "denver": "denver nuggets", "denver nuggets": "denver nuggets",
    "pistons": "detroit pistons", "det": "detroit pistons", "detroit": "detroit pistons", "detroit pistons": "detroit pistons",
    "warriors": "golden state warriors", "gsw": "golden state warriors", "golden state": "golden state warriors", "golden state warriors": "golden state warriors",
    "rockets": "houston rockets", "hou": "houston rockets", "houston": "houston rockets", "houston rockets": "houston rockets",
    "pacers": "indiana pacers", "ind": "indiana pacers", "indiana": "indiana pacers", "indiana pacers": "indiana pacers",
    "clippers": "los angeles clippers", "lac": "los angeles clippers", "la clippers": "los angeles clippers", "los angeles clippers": "los angeles clippers",
    "lakers": "los angeles lakers", "lal": "los angeles lakers", "la lakers": "los angeles lakers", "los angeles lakers": "los angeles lakers",
    "grizzlies": "memphis grizzlies", "mem": "memphis grizzlies", "memphis": "memphis grizzlies", "memphis grizzlies": "memphis grizzlies",
    "heat": "miami heat", "mia": "miami heat", "miami": "miami heat", "miami heat": "miami heat",
    "bucks": "milwaukee bucks", "mil": "milwaukee bucks", "milwaukee": "milwaukee bucks", "milwaukee bucks": "milwaukee bucks",
    "timberwolves": "minnesota timberwolves", "wolves": "minnesota timberwolves", "min": "minnesota timberwolves", "minnesota timberwolves": "minnesota timberwolves",
    "pelicans": "new orleans pelicans", "nop": "new orleans pelicans", "new orleans": "new orleans pelicans", "new orleans pelicans": "new orleans pelicans",
    "knicks": "new york knicks", "nyk": "new york knicks", "new york knicks": "new york knicks",
    "thunder": "oklahoma city thunder", "okc": "oklahoma city thunder", "oklahoma city": "oklahoma city thunder", "oklahoma city thunder": "oklahoma city thunder",
    "magic": "orlando magic", "orl": "orlando magic", "orlando": "orlando magic", "orlando magic": "orlando magic",
    "76ers": "philadelphia 76ers", "sixers": "philadelphia 76ers", "phi": "philadelphia 76ers", "philadelphia 76ers": "philadelphia 76ers",
    "suns": "phoenix suns", "phx": "phoenix suns", "phoenix": "phoenix suns", "phoenix suns": "phoenix suns",
    "trail blazers": "portland trail blazers", "blazers": "portland trail blazers", "por": "portland trail blazers", "portland": "portland trail blazers", "portland trail blazers": "portland trail blazers",
    "kings": "sacramento kings", "sac": "sacramento kings", "sacramento": "sacramento kings", "sacramento kings": "sacramento kings",
    "spurs": "san antonio spurs", "sas": "san antonio spurs", "san antonio": "san antonio spurs", "san antonio spurs": "san antonio spurs",
    "raptors": "toronto raptors", "tor": "toronto raptors", "toronto": "toronto raptors", "toronto raptors": "toronto raptors",
    "jazz": "utah jazz", "uta": "utah jazz", "utah": "utah jazz", "utah jazz": "utah jazz",
    "wizards": "washington wizards", "was": "washington wizards", "washington wizards": "washington wizards",

    # MLB
    "diamondbacks": "arizona diamondbacks", "d backs": "arizona diamondbacks", "arizona diamondbacks": "arizona diamondbacks",
    "braves": "atlanta braves", "atlanta braves": "atlanta braves",
    "orioles": "baltimore orioles", "baltimore orioles": "baltimore orioles",
    "red sox": "boston red sox", "boston red sox": "boston red sox",
    "cubs": "chicago cubs", "chicago cubs": "chicago cubs",
    "white sox": "chicago white sox", "chicago white sox": "chicago white sox",
    "reds": "cincinnati reds", "cincinnati reds": "cincinnati reds",
    "guardians": "cleveland guardians", "cleveland guardians": "cleveland guardians",
    "rockies": "colorado rockies", "colorado rockies": "colorado rockies",
    "tigers": "detroit tigers", "detroit tigers": "detroit tigers",
    "astros": "houston astros", "houston astros": "houston astros",
    "royals": "kansas city royals", "kansas city royals": "kansas city royals",
    "angels": "los angeles angels", "la angels": "los angeles angels", "los angeles angels": "los angeles angels",
    "dodgers": "los angeles dodgers", "la dodgers": "los angeles dodgers", "los angeles dodgers": "los angeles dodgers",
    "marlins": "miami marlins", "miami marlins": "miami marlins",
    "brewers": "milwaukee brewers", "milwaukee brewers": "milwaukee brewers",
    "twins": "minnesota twins", "minnesota twins": "minnesota twins",
    "mets": "new york mets", "ny mets": "new york mets", "new york mets": "new york mets",
    "yankees": "new york yankees", "ny yankees": "new york yankees", "new york yankees": "new york yankees",
    "athletics": "athletics", "oakland athletics": "athletics", "a's": "athletics",
    "phillies": "philadelphia phillies", "philadelphia phillies": "philadelphia phillies",
    "pirates": "pittsburgh pirates", "pittsburgh pirates": "pittsburgh pirates",
    "padres": "san diego padres", "san diego padres": "san diego padres",
    "giants": "san francisco giants", "sf giants": "san francisco giants", "san francisco giants": "san francisco giants",
    "mariners": "seattle mariners", "seattle mariners": "seattle mariners",
    "cardinals": "st louis cardinals", "st. louis cardinals": "st louis cardinals", "st louis cardinals": "st louis cardinals",
    "rays": "tampa bay rays", "tampa bay rays": "tampa bay rays",
    "rangers": "texas rangers", "texas rangers": "texas rangers",
    "blue jays": "toronto blue jays", "toronto blue jays": "toronto blue jays",
    "nationals": "washington nationals", "washington nationals": "washington nationals",

    # CPBL
    "ctbc brothers": "ctbc brothers", "chinatrust brothers": "ctbc brothers", "brothers": "ctbc brothers",
    "uni lions": "uni president lions", "uni-president lions": "uni president lions", "uni president lions": "uni president lions", "uni-president 7-eleven lions": "uni president lions", "tainan lions": "uni president lions",
    "rakuten monkeys": "rakuten monkeys", "monkeys": "rakuten monkeys",
    "wei chuan dragons": "wei chuan dragons", "dragons": "wei chuan dragons",
    "fubon guardians": "fubon guardians",
    "tsg hawks": "tsg hawks",

    # LoL
    "t1": "t1", "sk telecom t1": "t1", "t1 esports": "t1",
    "gen.g": "gen.g", "geng": "gen.g", "gen g": "gen.g",
    "hanwha life": "hanwha life esports", "hanwha life esports": "hanwha life esports", "hle": "hanwha life esports",
    "dplus kia": "dplus kia", "dk": "dplus kia", "damwon": "dplus kia",
    "kt rolster": "kt rolster", "kt": "kt rolster",
    "bilibili gaming": "bilibili gaming", "blg": "bilibili gaming",
    "top esports": "top esports", "tes": "top esports",
    "jd gaming": "jd gaming", "jdg": "jd gaming",
    "weibo gaming": "weibo gaming", "wbg": "weibo gaming",
    "lng esports": "lng esports", "lng": "lng esports",
    "g2 esports": "g2 esports", "g2": "g2 esports",
    "fnatic": "fnatic", "fnc": "fnatic",
    "flyquest": "flyquest", "fly": "flyquest",
    "ctbc flying oyster": "ctbc flying oyster", "cfo": "ctbc flying oyster",

    # Soccer
    "arsenal": "arsenal", "arsenal fc": "arsenal",
    "chelsea": "chelsea", "chelsea fc": "chelsea",
    "liverpool": "liverpool", "liverpool fc": "liverpool",
    "man city": "manchester city", "manchester city": "manchester city", "manchester city fc": "manchester city",
    "man utd": "manchester united", "man united": "manchester united", "manchester united": "manchester united",
    "tottenham": "tottenham hotspur", "tottenham hotspur": "tottenham hotspur",
    "newcastle": "newcastle united", "newcastle united": "newcastle united",
    "aston villa": "aston villa", "west ham": "west ham united", "west ham united": "west ham united",
    "brighton": "brighton and hove albion", "brighton & hove albion": "brighton and hove albion",
    "nottingham forest": "nottingham forest", "fulham": "fulham", "brentford": "brentford", "everton": "everton",
    "crystal palace": "crystal palace", "bournemouth": "afc bournemouth", "wolves": "wolverhampton wanderers", "wolverhampton": "wolverhampton wanderers",
    "real madrid": "real madrid", "barcelona": "fc barcelona", "fc barcelona": "fc barcelona",
    "atletico madrid": "atletico madrid", "bayern munich": "bayern munich", "bayern": "bayern munich",
    "borussia dortmund": "borussia dortmund", "dortmund": "borussia dortmund",
    "inter milan": "inter milan", "inter": "inter milan", "ac milan": "ac milan", "juventus": "juventus",
    "paris saint germain": "paris saint germain", "paris saint-germain": "paris saint germain", "psg": "paris saint germain",
}

CANONICAL_TO_ZH: Dict[str, str] = {
    # NBA
    "atlanta hawks": "老鷹", "boston celtics": "塞爾提克", "brooklyn nets": "籃網",
    "charlotte hornets": "黃蜂", "chicago bulls": "公牛", "cleveland cavaliers": "騎士",
    "dallas mavericks": "獨行俠", "denver nuggets": "金塊", "detroit pistons": "活塞",
    "golden state warriors": "勇士", "houston rockets": "火箭", "indiana pacers": "溜馬",
    "los angeles clippers": "快艇", "los angeles lakers": "湖人", "memphis grizzlies": "灰熊",
    "miami heat": "熱火", "milwaukee bucks": "公鹿", "minnesota timberwolves": "灰狼",
    "new orleans pelicans": "鵜鶘", "new york knicks": "尼克", "oklahoma city thunder": "雷霆",
    "orlando magic": "魔術", "philadelphia 76ers": "76人", "phoenix suns": "太陽",
    "portland trail blazers": "拓荒者", "sacramento kings": "國王", "san antonio spurs": "馬刺",
    "toronto raptors": "暴龍", "utah jazz": "爵士", "washington wizards": "巫師",
    # CPBL
    "ctbc brothers": "中信兄弟", "uni president lions": "統一獅", "rakuten monkeys": "樂天桃猿",
    "wei chuan dragons": "味全龍", "fubon guardians": "富邦悍將", "tsg hawks": "台鋼雄鷹",
    # Soccer
    "arsenal": "兵工廠", "chelsea": "切爾西", "liverpool": "利物浦",
    "manchester city": "曼城", "manchester united": "曼聯", "tottenham hotspur": "熱刺",
    "newcastle united": "紐卡索", "aston villa": "維拉", "real madrid": "皇馬",
    "fc barcelona": "巴塞隆納", "atletico madrid": "馬競", "bayern munich": "拜仁慕尼黑",
    "borussia dortmund": "多特蒙德", "inter milan": "國米", "ac milan": "AC米蘭",
    "juventus": "尤文圖斯", "paris saint germain": "巴黎聖日耳曼",
}


def clean_team_text(name: str) -> str:
    if not name:
        return ""
    # 剝除括號附註 (例如 "洛杉磯道奇 (LAD)")
    s = re.sub(r"\([^)]*\)", "", name).strip().lower()
    s = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def canonicalize_team(name: str, league_hint: str = "") -> str:
    """將任意語言（繁中 / 英文簡寫 / 全名）隊名轉換為標準 Canonical Key"""
    raw_zh = re.sub(r"\([^)]*\)", "", name or "").strip()
    if raw_zh in ZH_TO_CANONICAL:
        # 若為中職/足球與 NBA/MLB 重複名稱，按聯賽提示消歧義
        if raw_zh == "勇士" and league_hint.upper() == "MLB":
            return "atlanta braves"
        if raw_zh == "巨人" and league_hint.upper() == "NPB":
            return "yomiuri giants"
        return ZH_TO_CANONICAL[raw_zh]

    cleaned = clean_team_text(name)
    if not cleaned:
        return ""

    # 先精確查英文表
    if cleaned in EN_TO_CANONICAL:
        return EN_TO_CANONICAL[cleaned]

    # 部分詞組查表 (長字串優先)
    for k in sorted(ZH_TO_CANONICAL.keys(), key=len, reverse=True):
        if k in raw_zh:
            return ZH_TO_CANONICAL[k]
    for k in sorted(EN_TO_CANONICAL.keys(), key=len, reverse=True):
        if len(k) >= 4 and (f" {k} " in f" {cleaned} "):
            return EN_TO_CANONICAL[k]

    return cleaned


def get_zh_display_name(canonical: str, fallback: str = "") -> str:
    if canonical in CANONICAL_TO_ZH:
        return CANONICAL_TO_ZH[canonical]
    return fallback or canonical.title()


def match_two_teams(
    team1_a: str, team2_a: str,
    team1_b: str, team2_b: str,
    league_hint: str = "",
) -> Optional[Tuple[int, int]]:
    """
    比對兩個盤口是否為同一對戰組合，並回傳索引對齊元組：
    (0, 1) 表示 A.team1 == B.team1 且 A.team2 == B.team2
    (1, 0) 表示 A.team1 == B.team2 且 A.team2 == B.team1 (主客場寫法反置，如美盤客@主 vs 歐盤主v客)
    None 表示不匹配
    """
    c1_a = canonicalize_team(team1_a, league_hint)
    c2_a = canonicalize_team(team2_a, league_hint)
    c1_b = canonicalize_team(team1_b, league_hint)
    c2_b = canonicalize_team(team2_b, league_hint)

    if not all([c1_a, c2_a, c1_b, c2_b]):
        return None

    def _same(a: str, b: str) -> bool:
        if a == b:
            return True
        stop = {"fc", "afc", "sc", "cf", "esports", "gaming", "team", "club", "city", "united"}
        ta = set(a.split()) - stop
        tb = set(b.split()) - stop
        if ta and tb and (ta == tb or (len(ta) >= 1 and len(tb) >= 1 and (ta.issubset(tb) or tb.issubset(ta)))):
            return True
        return False

    if _same(c1_a, c1_b) and _same(c2_a, c2_b):
        return (0, 1)
    if _same(c1_a, c2_b) and _same(c2_a, c1_b):
        return (1, 0)
    return None
