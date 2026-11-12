"""
1/2 可投注目標盤口：台灣運彩 (TSL) 公開賠率與單場/串關標記擷取器 (radar/scrapers/tsl_scraper.py)
透過玩運彩公開台彩盤口頁 (playsport.cc/predict/games) 解析台灣運彩最新賠率，
支援：不讓分 (獨贏 / 足球主和客)、讓分 (SPREAD)、大小分 (TOTAL)，
並透過 livescore / 賽事表線索判定「單場」vs「⚠️ 需串關」(未確認開放單場者保守標為需串關提醒)。
"""
import re
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from curl_cffi import requests as creq
from bs4 import BeautifulSoup
from ..models import SourceOddsQuote
from ..devig import devig_decimal_odds
from ..matcher import canonicalize_team, get_zh_display_name

# Playsport 聯盟 ID 對應表
PLAYSPORT_LEAGUES = [
    {"aid": 3, "league": "NBA", "sport": "basketball", "three_way": False},
    {"aid": 4, "league": "SOCCER", "sport": "soccer", "three_way": True},
    {"aid": 91, "league": "NHL", "sport": "hockey", "three_way": False},
    {"aid": 1, "league": "MLB", "sport": "baseball", "three_way": False},
    {"aid": 2, "league": "NPB", "sport": "baseball", "three_way": False},
    {"aid": 6, "league": "CPBL", "sport": "baseball", "three_way": False},
]


class TSLRadarScraper:
    BASE_URL = "https://www.playsport.cc"

    def fetch_quotes(self) -> Tuple[List[SourceOddsQuote], Dict[str, Any]]:
        t0 = time.time()
        quotes: List[SourceOddsQuote] = []
        errors: List[str] = []
        seen_gameids: Set[str] = set()

        for cfg in PLAYSPORT_LEAGUES:
            aid = cfg["aid"]
            try:
                # 先抓該聯賽的 livescore 以比對論壇/即時標記中有提到的「台彩單場」隊伍
                single_hints = self._fetch_single_game_hints(aid)

                for gameday in ("today", "tomorrow"):
                    url = f"{self.BASE_URL}/predict/games?allianceid={aid}&gameday={gameday}"
                    resp = creq.get(url, impersonate="chrome", timeout=10)
                    if resp.status_code != 200:
                        continue
                    soup = BeautifulSoup(resp.text, "html.parser")
                    title_txt = soup.title.get_text(strip=True) if soup.title else ""
                    # 若某聯賽目前休賽被導回 NBA，只允許 aid=3 解析 NBA，避免重複抓錯聯賽
                    if aid != 3 and "NBA" in title_txt:
                        continue

                    parsed = self._parse_games_table(soup, cfg, single_hints, seen_gameids, gameday)
                    quotes.extend(parsed)
            except Exception as e:
                errors.append(f"aid={aid}: {str(e)[:70]}")

        latency_ms = int((time.time() - t0) * 1000)
        health = {
            "source": "tsl",
            "display_name": "台灣運彩 (TSL)",
            "role": "target",
            "status": "ok" if quotes else ("error" if errors else "degraded"),
            "matches_count": len(quotes),
            "latency_ms": latency_ms,
            "message": "; ".join(errors[:2]) if errors else f"已擷取台灣運彩 {len(quotes)} 個盤口",
        }
        return quotes, health

    def _fetch_single_game_hints(self, aid: int) -> Set[str]:
        """從玩運彩即時頁面摘要中萃取有明確標註「台彩單場 / 單場」之對戰關鍵字"""
        hints: Set[str] = set()
        try:
            r = creq.get(f"{self.BASE_URL}/livescore?allianceid={aid}", impersonate="chrome", timeout=8)
            if r.status_code != 200:
                return hints
            # 例: 《獨行俠🆚️灰狼》台彩單場
            for m in re.finditer(r"《([^》]+)》[^<]{0,20}(?:台彩單場|運彩單場|單場)", r.text):
                pair = m.group(1)
                for token in re.split(r"[🆚️vsVS/\s]+", pair):
                    t = token.strip()
                    if len(t) >= 2:
                        hints.add(t)
        except Exception:
            pass
        return hints

    def _parse_games_table(
        self,
        soup: BeautifulSoup,
        cfg: Dict[str, Any],
        single_hints: Set[str],
        seen_gameids: Set[str],
        gameday: str,
    ) -> List[SourceOddsQuote]:
        quotes: List[SourceOddsQuote] = []
        trs = soup.select("tr[gameid]")
        # 依 gameid 分組 (2-way 通常 2 列、足球 3-way 3 列)
        grouped: Dict[str, List[Any]] = {}
        for tr in trs:
            gid = tr.get("gameid", "")
            if not gid or gid in seen_gameids:
                continue
            grouped.setdefault(gid, []).append(tr)

        for gid, rows in grouped.items():
            seen_gameids.add(gid)
            if len(rows) < 2:
                continue

            # 足球 3-way (客 / 主 / 和) 與一般 2-way (客 / 主) 分開解析
            if cfg["three_way"] and len(rows) >= 3:
                quotes.extend(self._parse_three_way(gid, rows, cfg, single_hints, gameday))
            else:
                quotes.extend(self._parse_two_way(gid, rows, cfg, single_hints, gameday))
        return quotes

    @staticmethod
    def _extract_odd_and_line(td) -> Tuple[Optional[float], Optional[float]]:
        if not td:
            return None, None
        txt = td.get_text(" ", strip=True)
        # 典型格式: "客 +10.5 , 1.66" 或 "主 1.16" 或 "大 221.5 , 1.75"
        line_val: Optional[float] = None
        odd_val: Optional[float] = None
        m_pair = re.search(r"([+-]?\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)", txt)
        if m_pair:
            line_val = float(m_pair.group(1))
            odd_val = float(m_pair.group(2))
        else:
            m_single = re.search(r"(\d+\.\d+)", txt)
            if m_single:
                odd_val = float(m_single.group(1))
        if odd_val is not None and odd_val <= 1.0:
            odd_val = None
        return line_val, odd_val

    def _is_single_game(self, team_a_zh: str, team_b_zh: str, single_hints: Set[str]) -> bool:
        for t in (team_a_zh, team_b_zh):
            for h in single_hints:
                if h in t or t in h:
                    return True
        return False

    def _parse_two_way(
        self,
        gid: str,
        rows: List[Any],
        cfg: Dict[str, Any],
        single_hints: Set[str],
        gameday: str,
    ) -> List[SourceOddsQuote]:
        quotes: List[SourceOddsQuote] = []
        r_away, r_home = rows[0], rows[1]  # 玩運彩表格習慣：上列為客隊、下列為主隊

        gi = r_away.select_one("td.td-gameinfo")
        time_str = gi.select_one("h4").get_text(strip=True) if gi and gi.select_one("h4") else ""
        game_no = gi.select_one("h3").get_text(strip=True) if gi and gi.select_one("h3") else gid

        away_el = r_away.select_one("td.td-teaminfo a, td.td-teaminfo h3")
        home_el = r_home.select_one("td.td-teaminfo a, td.td-teaminfo h3")
        away_zh = away_el.get_text(strip=True) if away_el else ""
        home_zh = home_el.get_text(strip=True) if home_el else ""
        if not away_zh or not home_zh:
            return []

        league = cfg["league"]
        home_canon = canonicalize_team(home_zh, league)
        away_canon = canonicalize_team(away_zh, league)
        is_single = self._is_single_game(home_zh, away_zh, single_hints)
        min_legs = 1 if is_single else 2
        start_label = f"{'今日' if gameday == 'today' else '明日'} {time_str}".strip()

        # 1. 不讓分 (Moneyline) — 注意順序標準化為 [Home, Away]
        _, away_ml = self._extract_odd_and_line(r_away.select_one("td.td-bank-bet03"))
        _, home_ml = self._extract_odd_and_line(r_home.select_one("td.td-bank-bet03"))
        if home_ml and away_ml:
            dv = devig_decimal_odds([home_ml, away_ml], use_power=True)
            quotes.append(SourceOddsQuote(
                source="tsl",
                league=league,
                sport=cfg["sport"],
                home_team=home_canon or home_zh,
                away_team=away_canon or away_zh,
                home_team_zh=home_zh,
                away_team_zh=away_zh,
                start_time=start_label,
                market_type="ML",
                outcome_names=[home_zh, away_zh],
                raw_odds=[home_ml, away_ml],
                true_probs=dv["true_probs"],
                fair_odds=dv["fair_odds"],
                vig_pct=dv["vig_pct"],
                single_game_allowed=is_single,
                min_parlay_legs=min_legs,
                match_url=f"https://www.playsport.cc/gamesData/battle?gameid={gid}&allianceid={cfg['aid']}",
                extra={"tsl_game_no": game_no},
            ))

        # 2. 讓分 (Spread) — [Home, Away] 含主隊讓分線
        away_sp_line, away_sp_odd = self._extract_odd_and_line(r_away.select_one("td.td-bank-bet01"))
        home_sp_line, home_sp_odd = self._extract_odd_and_line(r_home.select_one("td.td-bank-bet01"))
        if home_sp_odd and away_sp_odd and home_sp_line is not None:
            dv = devig_decimal_odds([home_sp_odd, away_sp_odd], use_power=True)
            quotes.append(SourceOddsQuote(
                source="tsl",
                league=league,
                sport=cfg["sport"],
                home_team=home_canon or home_zh,
                away_team=away_canon or away_zh,
                home_team_zh=home_zh,
                away_team_zh=away_zh,
                start_time=start_label,
                market_type="SPREAD",
                line=home_sp_line,
                outcome_names=[home_zh, away_zh],
                raw_odds=[home_sp_odd, away_sp_odd],
                true_probs=dv["true_probs"],
                fair_odds=dv["fair_odds"],
                vig_pct=dv["vig_pct"],
                single_game_allowed=is_single,
                min_parlay_legs=min_legs,
                match_url=f"https://www.playsport.cc/gamesData/battle?gameid={gid}&allianceid={cfg['aid']}",
                extra={"tsl_game_no": game_no, "away_line": away_sp_line},
            ))

        # 3. 大小 (Total) — [Over 大, Under 小]
        over_line, over_odd = self._extract_odd_and_line(r_away.select_one("td.td-bank-bet02"))
        under_line, under_odd = self._extract_odd_and_line(r_home.select_one("td.td-bank-bet02"))
        tot_line = over_line or under_line
        if over_odd and under_odd and tot_line is not None:
            dv = devig_decimal_odds([over_odd, under_odd], use_power=True)
            quotes.append(SourceOddsQuote(
                source="tsl",
                league=league,
                sport=cfg["sport"],
                home_team=home_canon or home_zh,
                away_team=away_canon or away_zh,
                home_team_zh=home_zh,
                away_team_zh=away_zh,
                start_time=start_label,
                market_type="TOTAL",
                line=tot_line,
                outcome_names=["大分", "小分"],
                raw_odds=[over_odd, under_odd],
                true_probs=dv["true_probs"],
                fair_odds=dv["fair_odds"],
                vig_pct=dv["vig_pct"],
                single_game_allowed=is_single,
                min_parlay_legs=min_legs,
                match_url=f"https://www.playsport.cc/gamesData/battle?gameid={gid}&allianceid={cfg['aid']}",
                extra={"tsl_game_no": game_no},
            ))

        return quotes

    def _parse_three_way(
        self,
        gid: str,
        rows: List[Any],
        cfg: Dict[str, Any],
        single_hints: Set[str],
        gameday: str,
    ) -> List[SourceOddsQuote]:
        quotes: List[SourceOddsQuote] = []
        r_away, r_home, r_draw = rows[0], rows[1], rows[2]

        gi = r_away.select_one("td.td-gameinfo")
        time_str = gi.select_one("h4").get_text(strip=True) if gi and gi.select_one("h4") else ""
        l_el = gi.select_one(".league-name, h2, span") if gi else None
        league_txt = l_el.get_text(strip=True) if l_el else ""
        league = "EPL" if "英超" in league_txt else ("UCL" if "歐冠" in league_txt else "SOCCER")

        teams = r_away.select("td.td-teaminfo a, td.td-teaminfo h3")
        # 足球在玩運彩有時兩隊都在 td-teaminfo 內
        if len(teams) >= 2:
            away_zh = teams[0].get_text(strip=True)
            home_zh = teams[1].get_text(strip=True)
        else:
            away_zh = teams[0].get_text(strip=True) if teams else ""
            home_el = r_home.select_one("td.td-teaminfo a, td.td-teaminfo h3")
            home_zh = home_el.get_text(strip=True) if home_el else ""
        if not away_zh or not home_zh:
            return []

        is_single = self._is_single_game(home_zh, away_zh, single_hints)
        min_legs = 1 if is_single else 2
        start_label = f"{'今日' if gameday == 'today' else '明日'} {time_str}".strip()

        _, away_ml = self._extract_odd_and_line(r_away.select_one("td.td-bank-bet03"))
        _, home_ml = self._extract_odd_and_line(r_home.select_one("td.td-bank-bet03"))
        _, draw_ml = self._extract_odd_and_line(r_draw.select_one("td.td-bank-bet03"))

        if home_ml and draw_ml and away_ml:
            dv = devig_decimal_odds([home_ml, draw_ml, away_ml], use_power=True)
            quotes.append(SourceOddsQuote(
                source="tsl",
                league=league,
                sport="soccer",
                home_team=canonicalize_team(home_zh, league) or home_zh,
                away_team=canonicalize_team(away_zh, league) or away_zh,
                home_team_zh=home_zh,
                away_team_zh=away_zh,
                start_time=start_label,
                market_type="ML",
                outcome_names=[home_zh, "和局", away_zh],
                raw_odds=[home_ml, draw_ml, away_ml],
                true_probs=dv["true_probs"],
                fair_odds=dv["fair_odds"],
                vig_pct=dv["vig_pct"],
                single_game_allowed=is_single,
                min_parlay_legs=min_legs,
                match_url=f"https://www.playsport.cc/gamesData/battle?gameid={gid}&allianceid={cfg['aid']}",
            ))
        return quotes
