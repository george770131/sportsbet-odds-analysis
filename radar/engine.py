"""
7 平台跨市場對齊與 +EV 比價核心引擎 (radar/engine.py)
5 家參考指標 (Polymarket / Kalshi / Pinnacle / Betfair / Bet365) vs.
2 家可投注目標 (台灣運彩 TSL / 澳洲 Sportsbet)
"""
import hashlib
from typing import Dict, List, Any, Optional, Tuple
import config
from .models import (
    SourceOddsQuote,
    BENCHMARK_SOURCES,
    TARGET_BOOKS,
    TOTAL_BENCHMARKS,
)
from .devig import compute_weighted_consensus, evaluate_ev
from .matcher import canonicalize_team, match_two_teams, get_zh_display_name


BENCHMARK_KEYS = [b["key"] for b in BENCHMARK_SOURCES]
BENCHMARK_META = {b["key"]: b for b in BENCHMARK_SOURCES}
TARGET_META = {t["key"]: t for t in TARGET_BOOKS}


class OddsComparisonEngine:
    def align_and_evaluate(
        self,
        all_quotes: List[SourceOddsQuote],
        min_benchmarks: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        將 5 家參考指標與 2 家可投注盤口依「賽事 + 玩法 + 盤口線」精準對齊，
        產出 Mobile-First 比價卡片清單。
        """
        now_str = config.get_taiwan_now_str("%Y-%m-%d %H:%M:%S")
        benchmark_quotes = [q for q in all_quotes if q.source in BENCHMARK_META]
        target_quotes = [q for q in all_quotes if q.source in TARGET_META]

        if not benchmark_quotes or not target_quotes:
            return []

        # 1. 將同場賽事的兩個可投注目標 (tsl, sportsbet) 先群組在一起，方便同一張卡片互相比價
        target_groups: List[Dict[str, Any]] = []
        for tq in target_quotes:
            placed = False
            for grp in target_groups:
                rep: SourceOddsQuote = grp["rep"]
                if rep.market_type != tq.market_type or rep.sport != tq.sport:
                    continue
                if len(rep.raw_odds) != len(tq.raw_odds):
                    continue
                align = match_two_teams(rep.home_team, rep.away_team, tq.home_team, tq.away_team, rep.league)
                if not align:
                    continue
                if not self._lines_compatible(rep, tq, align):
                    continue
                grp["targets"][tq.source] = (tq, align)
                placed = True
                break
            if not placed:
                target_groups.append({
                    "rep": tq,
                    "targets": {tq.source: (tq, (0, 1))},
                })

        cards: List[Dict[str, Any]] = []

        # 2. 為每個目標群組尋找所有符合的參考指標 (1/5 ~ 5/5)
        for grp in target_groups:
            rep: SourceOddsQuote = grp["rep"]
            n_legs = len(rep.raw_odds)
            matched_benchmarks: Dict[str, Tuple[SourceOddsQuote, Tuple[int, int]]] = {}

            for bq in benchmark_quotes:
                if bq.source in matched_benchmarks:
                    continue
                if bq.market_type != rep.market_type or bq.sport != rep.sport:
                    continue
                if len(bq.raw_odds) != n_legs:
                    continue
                align = match_two_teams(rep.home_team, rep.away_team, bq.home_team, bq.away_team, rep.league)
                if not align:
                    continue
                if not self._lines_compatible(rep, bq, align):
                    continue
                matched_benchmarks[bq.source] = (bq, align)

            if len(matched_benchmarks) < min_benchmarks:
                continue

            # 3. 依 rep 的順序 [Home, (Draw), Away] 重排各參考指標之真實勝率與明細
            probs_by_source: Dict[str, List[float]] = {}
            benchmarks_detail: Dict[str, Dict[str, Any]] = {}

            for b_key in BENCHMARK_KEYS:
                meta = BENCHMARK_META[b_key]
                if b_key not in matched_benchmarks:
                    benchmarks_detail[b_key] = {
                        "name": meta["name"],
                        "short": meta["short"],
                        "available": False,
                    }
                    continue
                bq, align = matched_benchmarks[b_key]
                reordered_probs = self._reorder_list(bq.true_probs, align)
                reordered_raw = self._reorder_list(bq.raw_odds, align)
                reordered_fair = self._reorder_list(bq.fair_odds, align)
                probs_by_source[b_key] = reordered_probs
                benchmarks_detail[b_key] = {
                    "name": meta["name"],
                    "short": meta["short"],
                    "available": True,
                    "raw_odds": [round(x, 3) for x in reordered_raw],
                    "fair_odds": [round(x, 3) for x in reordered_fair],
                    "true_probs_pct": [round(x * 100.0, 2) for x in reordered_probs],
                    "vig_pct": round(bq.vig_pct, 2),
                    "url": bq.match_url,
                }

            consensus_probs, consensus_fair_odds, valid_count = compute_weighted_consensus(probs_by_source)
            if valid_count < min_benchmarks or len(consensus_probs) != n_legs:
                continue

            # 4. 彙整兩家目標盤口在各選項的賠率 (對齊到 rep 順序)
            targets_detail: Dict[str, Dict[str, Any]] = {}
            for t_key in TARGET_META:
                if t_key not in grp["targets"]:
                    targets_detail[t_key] = {
                        "name": TARGET_META[t_key]["name"],
                        "available": False,
                    }
                    continue
                tq, align = grp["targets"][t_key]
                re_odds = self._reorder_list(tq.raw_odds, align)
                re_probs = self._reorder_list(tq.true_probs, align)
                re_fair = self._reorder_list(tq.fair_odds, align)
                targets_detail[t_key] = {
                    "name": TARGET_META[t_key]["name"],
                    "available": True,
                    "raw_odds": [round(x, 3) for x in re_odds],
                    "fair_odds": [round(x, 3) for x in re_fair],
                    "true_probs_pct": [round(x * 100.0, 2) for x in re_probs],
                    "vig_pct": round(tq.vig_pct, 2),
                    "single_game_allowed": tq.single_game_allowed,
                    "min_parlay_legs": tq.min_parlay_legs,
                    "url": tq.match_url,
                }

            # 5. 建立統一顯示隊名
            h_canon = canonicalize_team(rep.home_team, rep.league)
            a_canon = canonicalize_team(rep.away_team, rep.league)
            home_zh = rep.home_team_zh or get_zh_display_name(h_canon, rep.home_team)
            away_zh = rep.away_team_zh or get_zh_display_name(a_canon, rep.away_team)
            line_display = self._format_line(rep)
            match_key = f"{rep.league}:{h_canon}_vs_{a_canon}"

            if rep.market_type == "TOTAL":
                side_labels = ["over", "under"]
                sel_names = [f"大 {rep.line}", f"小 {rep.line}"]
            elif n_legs == 3:
                side_labels = ["home", "draw", "away"]
                sel_names = [home_zh, "和局", away_zh]
            elif rep.market_type == "SPREAD":
                side_labels = ["home", "away"]
                h_l = rep.line if rep.line is not None else 0.0
                a_l = -h_l
                sel_names = [f"{home_zh} ({h_l:+g})", f"{away_zh} ({a_l:+g})"]
            else:
                side_labels = ["home", "away"]
                sel_names = [home_zh, away_zh]

            # 6. 對每一個有開盤的目標盤口與其選項計算 EV% 與 Edge%
            for t_key, t_info in targets_detail.items():
                if not t_info.get("available"):
                    continue
                t_odds = t_info["raw_odds"]
                for idx in range(n_legs):
                    offered = float(t_odds[idx])
                    true_p = float(consensus_probs[idx])
                    ev_info = evaluate_ev(true_p, offered)
                    raw_id = f"{match_key}|{rep.market_type}|{line_display}|{t_key}|{side_labels[idx]}"
                    card_id = hashlib.md5(raw_id.encode("utf-8")).hexdigest()[:16]

                    cards.append({
                        "card_id": card_id,
                        "match_key": match_key,
                        "sport": rep.sport,
                        "league": rep.league,
                        "home_team": rep.home_team,
                        "away_team": rep.away_team,
                        "home_team_zh": home_zh,
                        "away_team_zh": away_zh,
                        "start_time_tw": rep.start_time or "近期開賽",
                        "is_live": rep.is_live,
                        "market_type": rep.market_type,
                        "line_display": line_display,
                        "target_book": t_key,
                        "target_book_name": TARGET_META[t_key]["name"],
                        "selection_name": sel_names[idx],
                        "selection_side": side_labels[idx],
                        "target_odds": round(offered, 3),
                        "single_game_allowed": t_info.get("single_game_allowed"),
                        "min_parlay_legs": t_info.get("min_parlay_legs", 1),
                        "valid_benchmark_count": valid_count,
                        "total_benchmarks": TOTAL_BENCHMARKS,
                        "consensus_prob": round(true_p, 5),
                        "consensus_fair_odds": round(consensus_fair_odds[idx], 3),
                        "ev_pct": ev_info["ev_pct"],
                        "edge_pct": ev_info["edge_pct"],
                        "is_positive_ev": ev_info["is_positive_ev"],
                        "benchmarks": benchmarks_detail,
                        "targets": targets_detail,
                        "updated_at": now_str,
                    })

        # 依 EV% 高到低排序
        cards.sort(key=lambda c: (c["ev_pct"], c["valid_benchmark_count"]), reverse=True)
        return cards

    @staticmethod
    def _lines_compatible(rep: SourceOddsQuote, other: SourceOddsQuote, align: Tuple[int, int]) -> bool:
        if rep.market_type == "ML":
            return True
        if rep.line is None or other.line is None:
            return False
        if rep.market_type == "TOTAL":
            return abs(float(rep.line) - float(other.line)) < 0.01
        if rep.market_type == "SPREAD":
            # 若隊伍順序相同，讓分值須相等；若反置，讓分值須相反數
            if align == (0, 1):
                return abs(float(rep.line) - float(other.line)) < 0.01
            return abs(float(rep.line) + float(other.line)) < 0.01
        return True

    @staticmethod
    def _reorder_list(vals: List[float], align: Tuple[int, int]) -> List[float]:
        if len(vals) == 2:
            return [vals[align[0]], vals[align[1]]]
        if len(vals) == 3:
            # Draw 固定在 index 1
            first = 0 if align[0] == 0 else 2
            second = 2 if first == 0 else 0
            return [vals[first], vals[1], vals[second]]
        return list(vals)

    @staticmethod
    def _format_line(q: SourceOddsQuote) -> str:
        if q.market_type == "ML" or q.line is None:
            return ""
        if q.market_type == "SPREAD":
            return f"{q.line:+g}"
        return f"{q.line:g}"
