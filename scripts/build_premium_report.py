#!/usr/bin/env python3
"""Build a premium GEO HTML report from live Dageno API data (real data only)."""

from __future__ import annotations

import argparse
import html
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests

BASE_URL = "https://api.dageno.ai/business/api/v1/open-api"
TIMEOUT = 30


@dataclass
class DateRange:
    start: str
    end: str


def to_start_iso(date_str: str) -> str:
    return f"{date_str}T00:00:00.000Z"


def to_end_iso(date_str: str) -> str:
    return f"{date_str}T23:59:59.999Z"


def previous_period(period: DateRange) -> DateRange:
    start = datetime.strptime(period.start, "%Y-%m-%d")
    end = datetime.strptime(period.end, "%Y-%m-%d")
    days = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)
    return DateRange(prev_start.strftime("%Y-%m-%d"), prev_end.strftime("%Y-%m-%d"))


class DagenoClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{BASE_URL}/{endpoint}"
        try:
            if method == "GET":
                resp = self.session.get(url, params=params, timeout=TIMEOUT)
            else:
                resp = self.session.post(url, json=json_data, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                return data
            return {"success": False, "code": -1, "message": "Non-object response", "data": data}
        except requests.RequestException as exc:
            body = ""
            if getattr(exc, "response", None) is not None and exc.response is not None:
                body = exc.response.text[:800]
            return {
                "success": False,
                "code": -1,
                "message": f"{exc}",
                "error_body": body,
                "data": {},
            }

    def geo_analysis(
        self,
        entity: str,
        metrics: List[str],
        analysis_type: str,
        dr: DateRange,
        ranking: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "target": {
                "entity": entity,
                "metrics": metrics,
                "filters": {
                    "dateRange": {
                        "startAt": to_start_iso(dr.start),
                        "endAt": to_end_iso(dr.end),
                    }
                },
            },
            "analysis": {"type": analysis_type},
        }
        if ranking:
            payload["analysis"]["ranking"] = ranking
        return self.request("geo/analysis", method="POST", json_data=payload)

    def fetch_paged(
        self,
        endpoint: str,
        dr: DateRange,
        base_params: Optional[Dict[str, Any]] = None,
        page_size: int = 100,
        max_pages: Optional[int] = None,
    ) -> Dict[str, Any]:
        params = dict(base_params or {})
        all_items: List[Dict[str, Any]] = []
        page = 1
        total_pages = 1
        last_response: Dict[str, Any] = {}

        while page <= total_pages:
            if max_pages is not None and page > max_pages:
                break
            req_params = {
                **params,
                "page": page,
                "pageSize": page_size,
                "startAt": to_start_iso(dr.start),
                "endAt": to_end_iso(dr.end),
            }
            resp = self.request(endpoint, params=req_params)
            last_response = resp
            data = resp.get("data") or {}
            items = data.get("items") if isinstance(data, dict) else None
            if not isinstance(items, list):
                items = []
            all_items.extend(items)

            pagination = (resp.get("meta") or {}).get("pagination") or {}
            tp = pagination.get("totalPages")
            if isinstance(tp, int) and tp > 0:
                total_pages = tp
            else:
                total_pages = 1
            if total_pages == 1:
                break
            page += 1

        if not last_response:
            last_response = {"success": False, "data": {"items": []}, "meta": {"pagination": {}}}

        merged = dict(last_response)
        merged.setdefault("data", {})
        if isinstance(merged["data"], dict):
            merged["data"]["items"] = all_items
        merged.setdefault("meta", {})
        if isinstance(merged["meta"], dict):
            merged["meta"].setdefault("pagination", {})
            merged["meta"]["pagination"]["fetchedItems"] = len(all_items)
            merged["meta"]["pagination"]["fetchedPages"] = page - 1 if page > 1 else 1
            if max_pages is not None and (merged["meta"]["pagination"].get("totalPages") or 1) > max_pages:
                merged["meta"]["pagination"]["truncated"] = True
                merged["meta"]["pagination"]["truncateReason"] = (
                    f"Large dataset capped at {max_pages} pages for preview performance"
                )
        return merged


def pick_brand_name(brand_info: Dict[str, Any], ranking_rows: List[Dict[str, Any]]) -> str:
    name = ((brand_info.get("data") or {}).get("name") or "").strip()
    if name:
        return name
    if ranking_rows:
        return str(ranking_rows[0].get("name") or "Brand")
    return "Brand"


def brand_row(ranking_rows: List[Dict[str, Any]], brand_name: str) -> Tuple[Optional[Dict[str, Any]], int]:
    if not ranking_rows:
        return None, 0
    bn = brand_name.lower().replace(".com", "").strip()
    for i, row in enumerate(ranking_rows):
        rn = str(row.get("name") or "").lower().replace(".com", "").strip()
        if bn and (bn in rn or rn in bn):
            return row, i + 1
    return None, 0


def safe_num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def pct_str(value: Optional[float], digits: int = 1) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}%"


def delta_str(current: Optional[float], prev: Optional[float], digits: int = 1) -> str:
    if current is None or prev is None:
        return "N/A"
    if prev == 0:
        if current == 0:
            return "0.0%"
        return "N/A"
    delta = (current - prev) / abs(prev) * 100
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.{digits}f}%"


def sentiment_label(score: Optional[float]) -> str:
    if score is None:
        return "Unknown"
    if score >= 75:
        return "Good health"
    if score >= 60:
        return "Watch closely"
    return "Needs action"


def growth_from_series(series: List[float]) -> Optional[float]:
    if len(series) < 4:
        return None
    mid = len(series) // 2
    left = [v for v in series[:mid] if v is not None]
    right = [v for v in series[mid:] if v is not None]
    if not left or not right:
        return None
    l_avg = sum(left) / len(left)
    r_avg = sum(right) / len(right)
    if l_avg == 0:
        return None
    return (r_avg - l_avg) / l_avg * 100


def extract_rows(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = ((resp.get("data") or {}).get("rows") or [])
    return rows if isinstance(rows, list) else []


def extract_items(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = ((resp.get("data") or {}).get("items") or [])
    return items if isinstance(items, list) else []


def json_pretty(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def format_intentions(raw: Any) -> str:
    if raw is None:
        return "N/A"
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        chunks: List[str] = []
        for item in raw:
            if isinstance(item, dict):
                label = str(item.get("i") or item.get("intent") or item.get("name") or "").strip()
                score = item.get("s") if item.get("s") is not None else item.get("score")
                if label and score is not None:
                    chunks.append(f"{label} ({safe_num(score, 0):.0f}%)")
                elif label:
                    chunks.append(label)
                else:
                    chunks.append(str(item))
            else:
                chunks.append(str(item))
        return ", ".join(chunks) if chunks else "N/A"
    if isinstance(raw, dict):
        label = str(raw.get("i") or raw.get("intent") or raw.get("name") or "").strip()
        score = raw.get("s") if raw.get("s") is not None else raw.get("score")
        if label and score is not None:
            return f"{label} ({safe_num(score, 0):.0f}%)"
        if label:
            return label
    return str(raw)


def build_trend_svg(labels_fmt: List[str], datasets: List[Dict[str, Any]]) -> str:
    if not labels_fmt or not datasets:
        return "<div style='padding:40px;color:#64748b;font-size:13px;'>Trend chart unavailable.</div>"
    width, height = 1100, 340
    left, right, top, bottom = 60, 20, 20, 48
    plot_w = width - left - right
    plot_h = height - top - bottom

    values: List[float] = []
    for ds in datasets:
        for v in ds.get("data", []):
            if isinstance(v, (int, float)):
                values.append(float(v))
    if not values:
        return "<div style='padding:40px;color:#64748b;font-size:13px;'>Trend chart unavailable.</div>"
    min_v, max_v = min(values), max(values)
    if max_v <= min_v:
        max_v = min_v + 1.0

    def x_of(i: int) -> float:
        if len(labels_fmt) <= 1:
            return left
        return left + (plot_w * i / (len(labels_fmt) - 1))

    def y_of(v: float) -> float:
        return top + (max_v - v) / (max_v - min_v) * plot_h

    grid = []
    for t in range(5):
        y = top + t * (plot_h / 4)
        grid.append(f"<line x1='{left}' y1='{y:.1f}' x2='{width-right}' y2='{y:.1f}' stroke='#e5e7eb' stroke-width='1' />")

    x_labels = []
    for i, lbl in enumerate(labels_fmt):
        x = x_of(i)
        x_labels.append(f"<text x='{x:.1f}' y='{height-16}' text-anchor='middle' font-size='11' fill='#64748b'>{html.escape(lbl)}</text>")

    y_labels = []
    for t in range(5):
        v = min_v + (4 - t) * ((max_v - min_v) / 4)
        y = top + t * (plot_h / 4) + 4
        y_labels.append(f"<text x='{left-8}' y='{y:.1f}' text-anchor='end' font-size='11' fill='#64748b'>{v:.1f}%</text>")

    lines = []
    for ds in datasets[:8]:
        color = (ds.get("itemStyle") or {}).get("color", "#2563eb")
        points = []
        for i, v in enumerate(ds.get("data", [])):
            if isinstance(v, (int, float)):
                points.append(f"{x_of(i):.1f},{y_of(float(v)):.1f}")
        if len(points) >= 2:
            lines.append(
                f"<polyline points='{' '.join(points)}' fill='none' stroke='{color}' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' />"
            )

    return (
        f"<svg viewBox='0 0 {width} {height}' width='100%' height='100%' xmlns='http://www.w3.org/2000/svg'>"
        f"{''.join(grid)}{''.join(lines)}{''.join(x_labels)}{''.join(y_labels)}</svg>"
    )


def build_section_analysis(title: str, lines: List[str]) -> str:
    body = "".join(f"<li>{html.escape(line)}</li>" for line in lines if line)
    if not body:
        body = "<li>No enough data for this section.</li>"
    return f"""
    <div class=\"analysis-box\">
      <div class=\"analysis-title\">{html.escape(title)}</div>
      <ul class=\"analysis-list\">{body}</ul>
    </div>
    """


def build_report_html(payload: Dict[str, Any]) -> str:
    brand_info = payload["brand_info"]
    ranking_rows = extract_rows(payload["brand_ranking_current"])
    ranking_rows_prev = extract_rows(payload["brand_ranking_previous"])
    trend_rows = extract_rows(payload["brand_trend_7d"])
    trend_30_rows = extract_rows(payload["brand_trend_30d"])
    topic_rows = extract_rows(payload["topic_ranking"])

    brand_name = pick_brand_name(brand_info, ranking_rows)
    my_row, rank = brand_row(ranking_rows, brand_name)
    prev_my_row, prev_rank = brand_row(ranking_rows_prev, brand_name)

    vis = safe_num((my_row or {}).get("visibility"), None)
    prev_vis = safe_num((prev_my_row or {}).get("visibility"), None) if prev_my_row else None

    summary_rows = extract_rows(payload["brand_summary_current"])
    prev_summary_rows = extract_rows(payload["brand_summary_previous"])
    sent = safe_num(summary_rows[0].get("sentiment"), None) if summary_rows else None
    prev_sent = safe_num(prev_summary_rows[0].get("sentiment"), None) if prev_summary_rows else None

    citations_total = int(
        ((payload["citation_urls"] or {}).get("meta") or {}).get("pagination", {}).get("total")
        or len(extract_items(payload["citation_urls"]))
    )
    citations_prev_total = int(
        ((payload["citation_urls_previous"] or {}).get("meta") or {}).get("pagination", {}).get("total")
        or len(extract_items(payload["citation_urls_previous"]))
    )

    all_brands = len(ranking_rows)
    leader = ranking_rows[0] if ranking_rows else {}
    leader_name = str(leader.get("name") or "N/A")
    leader_vis = safe_num(leader.get("visibility"), None)

    comp_gap_pct: Optional[float] = None
    if vis is not None and vis > 0 and leader_vis is not None:
        comp_gap_pct = (leader_vis - vis) / vis * 100

    trend_by_brand: Dict[str, List[Dict[str, Any]]] = {}
    for row in trend_rows:
        key = str(row.get("name") or "Unknown")
        trend_by_brand.setdefault(key, []).append(row)

    labels = sorted({str(r.get("date") or "") for r in trend_rows if r.get("date")})
    labels_fmt = [datetime.strptime(d, "%Y-%m-%d").strftime("%m/%d") if d else d for d in labels]
    datasets = []
    colors = ["#ec783b", "#4f46e5", "#14b8a6", "#e11d48", "#0ea5e9", "#f59e0b", "#8b5cf6"]
    for idx, (name, rows) in enumerate(sorted(trend_by_brand.items(), key=lambda kv: -safe_num(kv[1][0].get("visibility"), 0))[:8]):
        map_by_date = {str(r.get("date")): safe_num(r.get("visibility"), 0) * 100 for r in rows}
        datasets.append(
            {
                "name": name,
                "type": "line",
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"width": 3},
                "itemStyle": {"color": colors[idx % len(colors)]},
                "data": [map_by_date.get(d) for d in labels],
            }
        )
    trend_svg_fallback = build_trend_svg(labels_fmt, datasets)

    my_trend_30 = [safe_num(r.get("visibility"), 0) * 100 for r in trend_30_rows if str(r.get("name") or "").lower() == brand_name.lower()]
    growth_30 = growth_from_series(my_trend_30)

    topic_items = extract_items(payload["topics"])
    prompt_items = extract_items(payload["prompts"])
    citation_domain_items = extract_items(payload["citation_domains"])
    content_items = extract_items(payload["content_opportunities"])
    backlink_items = extract_items(payload["backlink_opportunities"])
    community_items = extract_items(payload["community_opportunities"])

    unique_community_items: List[Dict[str, Any]] = []
    seen_community = set()
    for item in community_items:
        key = (str(item.get("url") or "").strip().lower(), str(item.get("title") or "").strip().lower())
        if key in seen_community:
            continue
        seen_community.add(key)
        unique_community_items.append(item)

    # Keep API order, but diversify shown community cards across domains first.
    community_display_items: List[Dict[str, Any]] = []
    seen_domain = set()
    for item in unique_community_items:
        domain = str(item.get("domain") or "").strip().lower()
        if not item.get("url"):
            continue
        if domain and domain not in seen_domain:
            seen_domain.add(domain)
            community_display_items.append(item)
        if len(community_display_items) >= 8:
            break
    if len(community_display_items) < 8:
        picked = {str(x.get("url")) for x in community_display_items}
        for item in unique_community_items:
            u = str(item.get("url") or "")
            if not u or u in picked:
                continue
            community_display_items.append(item)
            picked.add(u)
            if len(community_display_items) >= 8:
                break

    rank_delta_text = "N/A"
    rank_change_class = "neutral"
    if rank and prev_rank:
        if rank < prev_rank:
            rank_delta_text = f"↑ {prev_rank - rank}"
            rank_change_class = "up"
        elif rank > prev_rank:
            rank_delta_text = f"↓ {rank - prev_rank}"
            rank_change_class = "down"
        else:
            rank_delta_text = "Stable"

    vis_pct = vis * 100 if vis is not None else None
    sent_score = sent
    mind_share_detail = f"#{rank} of {all_brands} brands" if rank else "N/A"

    visibility_lines = [
        f"Current visibility is {pct_str(vis_pct)}; previous period change is {delta_str(vis, prev_vis)}.",
        f"Current rank is #{rank if rank else 'N/A'} with rank movement: {rank_delta_text}.",
        f"Pain point: gap to leader ({leader_name}) is {pct_str(comp_gap_pct)} relative to your visibility." if comp_gap_pct is not None else "Pain point: leader gap cannot be computed from available data.",
    ]
    topic_lines = [
        f"Tracked topics: {len(topic_items)}; ranked topic rows: {len(topic_rows)}.",
        (
            f"Top topic by visibility is {topic_rows[0].get('topic', 'N/A')} at {pct_str(safe_num(topic_rows[0].get('visibility'), 0) * 100)}."
            if topic_rows
            else "No topic ranking rows returned for this period."
        ),
        "Pain point: low-sentiment topics should be prioritized for content optimization."
        if any(safe_num(t.get("sentiment"), 0) < 60 for t in topic_rows)
        else "Pain point: no severe low-sentiment topic detected in ranking rows.",
    ]
    citation_lines = [
        f"Total citation URLs: {citations_total}; previous period: {citations_prev_total}; change {delta_str(float(citations_total), float(citations_prev_total))}.",
        (
            f"Top citation domain: {citation_domain_items[0].get('domain', 'N/A')} ({citation_domain_items[0].get('citationCount', 0)} citations)."
            if citation_domain_items
            else "No citation domain data returned."
        ),
        "Pain point: citation concentration is high when top domain share dominates, indicating source diversity risk.",
    ]
    opportunity_lines = [
        f"Content opportunities: {len(content_items)}, backlink opportunities: {len(backlink_items)}, community opportunities: {len(unique_community_items)} (deduplicated).",
        (
            f"Highest content gap prompt: {content_items[0].get('prompt', '')[:90]}"
            if content_items
            else "No content opportunities returned."
        ),
        "Pain point: if high-priority backlink/community items are not executed quickly, competitor citation advantage will widen.",
    ]

    vis_analysis_html = build_section_analysis("Visibility Analysis", visibility_lines)
    topic_analysis_html = build_section_analysis("Topic Analysis", topic_lines)
    citation_analysis_html = build_section_analysis("Citation Analysis", citation_lines)
    opp_analysis_html = build_section_analysis("Opportunity Analysis", opportunity_lines)

    visibility_summary = (
        f"Summary: Visibility is {pct_str(vis_pct)} with rank #{rank if rank else 'N/A'}. "
        f"Momentum is {delta_str(vis, prev_vis)} vs the previous period. Recommendation: defend top-performing themes and improve low-sentiment content quality."
    )
    competitor_summary = (
        f"Summary: {all_brands} brands are tracked. Your visibility gap to leader {leader_name} is {pct_str(comp_gap_pct)}. "
        "Recommendation: prioritize high-visibility, high-commercial-intent topics to close the gap faster."
    )
    topic_summary = (
        f"Summary: {len(topic_rows)} core topics were returned; the current top topic is "
        f"{topic_rows[0].get('topic', 'N/A') if topic_rows else 'N/A'}. Recommendation: strengthen low-sentiment topics with FAQ and example-driven content."
    )
    citation_summary = (
        f"Summary: Total citation URLs this period are {citations_total}, with a change of {delta_str(float(citations_total), float(citations_prev_total))} vs the previous period. "
        "Recommendation: expand high-authority source coverage to reduce citation concentration risk."
    )
    prompt_summary = (
        f"Summary: {len(prompt_items)} prompts were analyzed and intent fields were converted into plain-language labels. "
        "Recommendation: prioritize prompts with high commercial intent but lower sentiment."
    )
    opp_summary = (
        f"Summary: {len(content_items)} content opportunities, {len(backlink_items)} backlink opportunities, and "
        f"{len(unique_community_items)} deduplicated community opportunities are available. Recommendation: execute high-priority, cross-platform opportunities first."
    )

    top_topics = ", ".join([str(t.get("topic") or "") for t in topic_rows[:2] if t.get("topic")]) or "N/A"
    exec_headline = (
        f"Overall, {brand_name} holds rank #{rank if rank else 'N/A'} this period, with visibility at {pct_str(vis_pct)} "
        f"and sentiment score at {f'{sent_score:.1f}' if sent_score is not None else 'N/A'}."
    )
    exec_key_findings = [
        f"Growth signal: visibility period-over-period is {delta_str(vis, prev_vis)}, and 30-day trend is {pct_str(growth_30)}.",
        f"Competitive pressure: the gap to leader {leader_name} is {pct_str(comp_gap_pct)} and still requires sustained catch-up.",
        f"Content focus: high-value topics include {top_topics}; these are strong candidates for additional investment.",
        "Channel status: community opportunities extend beyond Reddit and include YouTube, LinkedIn, and Quora domains.",
    ]
    exec_actions = [
        "Prioritize fixing low-sentiment but high-commercial-intent topic pages to improve conversion quality.",
        "Expand citation-friendly structured content around leading topics to increase AI citation probability.",
        "Run a cross-platform community distribution rhythm (Reddit + YouTube + Quora + LinkedIn) to avoid single-platform dependency.",
    ]

    comp_rows_html = "".join(
        f"""
        <tr>
          <td>{i+1}</td>
          <td>{html.escape(str(r.get('name') or ''))}{' <strong style="color:#ec783b">(You)</strong>' if (brand_name.lower() in str(r.get('name') or '').lower()) else ''}</td>
          <td>{pct_str(safe_num(r.get('visibility'), 0) * 100)}</td>
          <td>{pct_str(safe_num(r.get('citation'), 0) * 100, 2)}</td>
        </tr>
        """
        for i, r in enumerate(ranking_rows)
    )

    topic_rows_html = "".join(
        f"""
        <tr>
          <td>{i+1}</td>
          <td>{html.escape(str(t.get('topic') or ''))}</td>
          <td>{pct_str(safe_num(t.get('visibility'), 0) * 100)}</td>
          <td>{safe_num(t.get('sentiment'), 0):.1f}</td>
          <td>{pct_str(safe_num(t.get('citation'), 0) * 100, 2)}</td>
        </tr>
        """
        for i, t in enumerate(topic_rows)
    )

    domain_rows_html = "".join(
        f"""
        <tr>
          <td>{html.escape(str(d.get('domain') or ''))}</td>
          <td>{html.escape(str(d.get('domainType') or ''))}</td>
          <td>{int(safe_num(d.get('citationCount'), 0))}</td>
          <td>{pct_str(safe_num(d.get('citationRate'), 0) * 100, 2)}</td>
        </tr>
        """
        for d in citation_domain_items[:20]
    )

    prompt_rows_html = "".join(
        f"""
        <tr>
          <td>{html.escape(str(p.get('topic') or ''))}</td>
          <td>{html.escape(format_intentions(p.get('intentions')))}</td>
          <td>{pct_str(safe_num(p.get('visibility'), 0) * 100)}</td>
          <td>{safe_num(p.get('sentiment'), 0):.1f}</td>
          <td>{pct_str(safe_num(p.get('citationRate'), 0) * 100, 2)}</td>
        </tr>
        """
        for p in prompt_items[:30]
    )

    content_cards = "".join(
        f"<li><strong>{html.escape(str(x.get('topic') or 'Topic'))}</strong><br>{html.escape(str(x.get('prompt') or '')[:180])}</li>"
        for x in content_items[:8]
    ) or "<li>No data</li>"

    backlink_cards = "".join(
        f"<li><strong>{html.escape(str(x.get('domain') or 'Domain'))}</strong><br>priority {safe_num(x.get('priority'), 0):.1f}, prompts {int(safe_num(x.get('promptCount'), 0))}</li>"
        for x in backlink_items[:8]
    ) or "<li>No data</li>"

    community_chunks: List[str] = []
    for x in community_display_items:
        if not x.get("url"):
            continue
        title = str(x.get("title") or "").strip()
        if not title or title.lower().startswith("http"):
            title = str(x.get("prompt") or "Community opportunity").strip()[:120]
        community_chunks.append(
            f"""<li>
        <strong>{html.escape(str(x.get('domain') or 'Domain'))}</strong><br>
        {html.escape(title[:120])}<br>
        <a href="{html.escape(str(x.get('url') or '#'))}" target="_blank" rel="noopener noreferrer">Open source link</a>
        </li>"""
        )
    community_cards = "".join(community_chunks) or "<li>No data</li>"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    period = payload["period"]

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{html.escape(brand_name)} GEO Weekly Report</title>
  <script src=\"https://cdn.tailwindcss.com\"></script>
  <script src=\"https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js\"></script>
  <link href=\"https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Sora:wght@500;600;700;800&display=swap\" rel=\"stylesheet\" />
  <style>
    :root {{ --brand:#ec783b; --brand-deep:#ca5f25; --ink:#1d2433; --muted:#627084; --line:#eadfd6; --paper:rgba(255,255,255,.86); --shadow:0 18px 45px rgba(92,59,36,.08); }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family:'Manrope',sans-serif; color:var(--ink); background:radial-gradient(circle at top right, rgba(236,120,59,.10), transparent 26%), linear-gradient(180deg,#fffdfb 0%,#faf5f0 100%); }}
    h1,h2,h3,h4 {{ font-family:'Sora',sans-serif; letter-spacing:-.02em; }}
    .page {{ max-width:1200px; margin:0 auto; padding:24px; }}
    .hero {{ background:var(--paper); border:1px solid rgba(236,120,59,.12); border-radius:24px; box-shadow:var(--shadow); padding:24px; }}
    .pill {{ display:inline-flex; align-items:center; padding:5px 12px; border-radius:999px; font-size:12px; font-weight:700; background:rgba(236,120,59,.12); color:var(--brand-deep); }}
    .kpi-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin-top:18px; }}
    .kpi {{ background:#fff; border:1px solid #f1e7dd; border-radius:16px; padding:16px; }}
    .kpi .label {{ color:var(--muted); font-size:12px; text-transform:uppercase; font-weight:700; letter-spacing:.05em; }}
    .kpi .value {{ font-size:30px; font-weight:800; margin-top:8px; line-height:1; }}
    .kpi .delta {{ font-size:12px; margin-top:8px; font-weight:700; }}
    .up {{ color:#10b981; }} .down {{ color:#ef4444; }} .neutral {{ color:#64748b; }}
    .section {{ margin-top:20px; background:var(--paper); border:1px solid rgba(236,120,59,.12); border-radius:20px; box-shadow:var(--shadow); padding:20px; }}
    .section-title {{ display:flex; justify-content:space-between; align-items:baseline; margin-bottom:12px; }}
    .section-title h3 {{ margin:0; font-size:20px; }}
    .subtle {{ color:var(--muted); font-size:13px; }}
    .section-summary {{ margin:2px 0 12px; font-size:14px; color:#334155; font-weight:600; }}
    .exec-summary {{ margin-top:14px; background:#fff; border:1px solid #f1e7dd; border-radius:16px; padding:16px; }}
    .exec-title {{ margin:0 0 8px; font-size:16px; font-weight:800; color:#1f2937; }}
    .chip-row {{ display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 10px; }}
    .chip {{ display:inline-block; padding:5px 10px; border-radius:999px; font-size:12px; font-weight:700; }}
    .chip.good {{ background:rgba(16,185,129,.12); color:#065f46; }}
    .chip.warn {{ background:rgba(245,158,11,.15); color:#92400e; }}
    .chip.info {{ background:rgba(59,130,246,.12); color:#1d4ed8; }}
    .exec-list {{ margin:6px 0 0; padding-left:18px; }}
    .exec-list li {{ margin:5px 0; font-size:13px; color:#334155; }}
    .chart {{ width:100%; height:360px; border-radius:12px; background:#fff; border:1px solid #f1e7dd; position:relative; overflow:hidden; }}
    .chart-fallback {{ position:absolute; inset:0; }}
    table {{ width:100%; border-collapse:collapse; background:#fff; border-radius:12px; overflow:hidden; border:1px solid #f1e7dd; }}
    th,td {{ padding:10px 12px; border-bottom:1px solid #f4ede6; font-size:13px; text-align:left; }}
    th {{ background:#fff7f1; font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:#6d7788; }}
    .analysis-box {{ margin-top:12px; padding:14px 16px; border-left:4px solid var(--brand); background:linear-gradient(135deg, rgba(236,120,59,.10), rgba(255,247,241,.9)); border-radius:0 14px 14px 0; }}
    .analysis-title {{ font-weight:800; margin-bottom:6px; font-size:13px; color:#243244; }}
    .analysis-list {{ margin:0; padding-left:18px; }}
    .analysis-list li {{ margin:5px 0; font-size:13px; color:#304155; }}
    .split {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
    .list-card {{ background:#fff; border:1px solid #f1e7dd; border-radius:12px; padding:12px; }}
    .list-card ul {{ margin:0; padding-left:18px; }}
    .list-card li {{ margin:8px 0; font-size:13px; }}
    @media (max-width: 980px) {{ .kpi-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .split {{ grid-template-columns:1fr; }} .page {{ padding:14px; }} }}
  </style>
</head>
<body>
  <div class=\"page\">
    <section class=\"hero\">
      <div style=\"display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;\">
        <div>
          <div class=\"pill\">Weekly GEO Report</div>
          <h1 style=\"margin:10px 0 6px; font-size:34px;\">{html.escape(brand_name)}</h1>
          <div class=\"subtle\">Period: {period.start} to {period.end} | Generated: {now}</div>
        </div>
        <div style=\"text-align:right; min-width:250px;\">
          <div class=\"subtle\" style=\"font-weight:700; text-transform:uppercase;\">Weekly Performance Summary</div>
          <div style=\"font-size:28px; font-weight:800; margin-top:6px;\">{pct_str(vis_pct)}</div>
          <div class=\"subtle\">Visibility | {delta_str(vis, prev_vis)} vs previous period</div>
        </div>
      </div>

      <div class=\"kpi-grid\">
        <div class=\"kpi\"><div class=\"label\">AI Visibility</div><div class=\"value\">{pct_str(vis_pct)}</div><div class=\"delta {'up' if str(delta_str(vis, prev_vis)).startswith('+') else 'down' if str(delta_str(vis, prev_vis)).startswith('-') else 'neutral'}\">{delta_str(vis, prev_vis)}</div></div>
        <div class=\"kpi\"><div class=\"label\">Competitor Ranking</div><div class=\"value\">#{rank if rank else 'N/A'}</div><div class=\"delta {rank_change_class}\">{rank_delta_text}</div></div>
        <div class=\"kpi\"><div class=\"label\">Sentiment Score</div><div class=\"value\">{f'{sent_score:.1f}' if sent_score is not None else 'N/A'}</div><div class=\"delta {'up' if str(delta_str(sent, prev_sent)).startswith('+') else 'down' if str(delta_str(sent, prev_sent)).startswith('-') else 'neutral'}\">{delta_str(sent, prev_sent)}</div></div>
        <div class=\"kpi\"><div class=\"label\">Total Citations</div><div class=\"value\">{citations_total}</div><div class=\"delta {'up' if str(delta_str(float(citations_total), float(citations_prev_total))).startswith('+') else 'down' if str(delta_str(float(citations_total), float(citations_prev_total))).startswith('-') else 'neutral'}\">{delta_str(float(citations_total), float(citations_prev_total))}</div></div>
      </div>

      <div class=\"exec-summary\">
        <h3 class=\"exec-title\">Executive Summary</h3>
        <div class=\"section-summary\">{html.escape(exec_headline)}</div>
        <div class=\"chip-row\">
          <span class=\"chip info\">Visibility {pct_str(vis_pct)}</span>
          <span class=\"chip {'good' if str(delta_str(vis, prev_vis)).startswith('+') else 'warn'}\">Trend {delta_str(vis, prev_vis)}</span>
          <span class=\"chip {'good' if (sent_score is not None and sent_score >= 70) else 'warn'}\">Sentiment {f'{sent_score:.1f}' if sent_score is not None else 'N/A'}</span>
          <span class=\"chip warn\">Gap {pct_str(comp_gap_pct)} vs {html.escape(leader_name)}</span>
        </div>
        <ul class=\"exec-list\">
          {"".join(f"<li>{html.escape(x)}</li>" for x in exec_key_findings)}
        </ul>
        <ul class=\"exec-list\">
          {"".join(f"<li><strong>Recommendation:</strong> {html.escape(x)}</li>" for x in exec_actions)}
        </ul>
      </div>

      <div class=\"section\" style=\"margin-top:16px;\">
        <div class=\"section-title\"><h3>AI Insights</h3><span class=\"subtle\">No duplicate metrics, complementary interpretation</span></div>
        <div class=\"kpi-grid\" style=\"margin-top:0\">
          <div class=\"kpi\"><div class=\"label\">Mind Share</div><div class=\"value\">{pct_str(vis_pct)}</div><div class=\"delta neutral\">{mind_share_detail}</div></div>
          <div class=\"kpi\"><div class=\"label\">Sentiment Health</div><div class=\"value\">{f'{sent_score:.1f}/100' if sent_score is not None else 'N/A'}</div><div class=\"delta neutral\">{sentiment_label(sent_score)}</div></div>
          <div class=\"kpi\"><div class=\"label\">Competitive Gap</div><div class=\"value\">{pct_str(comp_gap_pct)}</div><div class=\"delta neutral\">Behind {html.escape(leader_name)}</div></div>
          <div class=\"kpi\"><div class=\"label\">30-Day Trend</div><div class=\"value\">{pct_str(growth_30)}</div><div class=\"delta neutral\">30-day visibility momentum</div></div>
        </div>
      </div>
    </section>

    <section class=\"section\">
      <div class=\"section-title\"><h3>Visibility Trend</h3><span class=\"subtle\">7-day trend by competitor</span></div>
      <p class=\"section-summary\">{html.escape(visibility_summary)}</p>
      <div id=\"trendChart\" class=\"chart\"><div id=\"trendFallback\" class=\"chart-fallback\">{trend_svg_fallback}</div></div>
      {vis_analysis_html}
    </section>

    <section class=\"section\">
      <div class=\"section-title\"><h3>Competitor Ranking</h3><span class=\"subtle\">All rows from GEO ranking API</span></div>
      <p class=\"section-summary\">{html.escape(competitor_summary)}</p>
      <table><thead><tr><th>Rank</th><th>Brand</th><th>Visibility</th><th>Citation</th></tr></thead><tbody>{comp_rows_html or '<tr><td colspan="4">No data</td></tr>'}</tbody></table>
    </section>

    <section class=\"section\">
      <div class=\"section-title\"><h3>Topic Performance</h3><span class=\"subtle\">Topic ranking + topic list</span></div>
      <p class=\"section-summary\">{html.escape(topic_summary)}</p>
      <table><thead><tr><th>#</th><th>Topic</th><th>Visibility</th><th>Sentiment</th><th>Citation</th></tr></thead><tbody>{topic_rows_html or '<tr><td colspan="5">No data</td></tr>'}</tbody></table>
      {topic_analysis_html}
    </section>

    <section class=\"section\">
      <div class=\"section-title\"><h3>Citation Sources</h3><span class=\"subtle\">Domain and URL citation data</span></div>
      <p class=\"section-summary\">{html.escape(citation_summary)}</p>
      <table><thead><tr><th>Domain</th><th>Type</th><th>Citations</th><th>Rate</th></tr></thead><tbody>{domain_rows_html or '<tr><td colspan="4">No data</td></tr>'}</tbody></table>
      {citation_analysis_html}
    </section>

    <section class=\"section\">
      <div class=\"section-title\"><h3>Prompt Intelligence</h3><span class=\"subtle\">Prompts and core quality metrics</span></div>
      <p class=\"section-summary\">{html.escape(prompt_summary)}</p>
      <table><thead><tr><th>Topic</th><th>Intent</th><th>Visibility</th><th>Sentiment</th><th>Citation Rate</th></tr></thead><tbody>{prompt_rows_html or '<tr><td colspan="5">No data</td></tr>'}</tbody></table>
    </section>

    <section class=\"section\">
      <div class=\"section-title\"><h3>Action Opportunities</h3><span class=\"subtle\">Content / Backlink / Community</span></div>
      <p class=\"section-summary\">{html.escape(opp_summary)}</p>
      <div class=\"split\">
        <div class=\"list-card\"><h4>Content</h4><ul>{content_cards}</ul></div>
        <div class=\"list-card\"><h4>Backlink</h4><ul>{backlink_cards}</ul></div>
        <div class=\"list-card\"><h4>Community</h4><ul>{community_cards}</ul></div>
      </div>
      {opp_analysis_html}
    </section>
  </div>

  <script>
    const trendOption = {{
      backgroundColor: '#fff',
      tooltip: {{ trigger: 'axis' }},
      legend: {{ type: 'scroll', top: 8 }},
      grid: {{ left: 40, right: 20, top: 48, bottom: 28 }},
      xAxis: {{ type: 'category', data: {json.dumps(labels_fmt, ensure_ascii=False)} }},
      yAxis: {{ type: 'value', axisLabel: {{ formatter: '{{value}}%' }} }},
      series: {json.dumps(datasets, ensure_ascii=False)}
    }};
    const trendContainer = document.getElementById('trendChart');
    const fallbackNode = document.getElementById('trendFallback');
    if (window.echarts && trendContainer) {{
      try {{
        const trendChart = echarts.init(trendContainer);
        trendChart.setOption(trendOption);
        if (fallbackNode) fallbackNode.style.display = 'none';
        window.addEventListener('resize', () => trendChart.resize());
      }} catch (e) {{
        if (fallbackNode) fallbackNode.style.display = 'block';
      }}
    }}
  </script>
</body>
</html>
"""


def fetch_all_data(
    client: DagenoClient,
    period: DateRange,
    prompt_details_limit: Optional[int],
    max_pages_per_endpoint: Optional[int],
) -> Dict[str, Any]:
    prev = previous_period(period)

    print("[1/17] brand")
    brand_info = client.request("brand")

    print("[2/17] brand summary current")
    brand_summary_current = client.geo_analysis("brand", ["visibility", "citation", "sentiment"], "summary", period)
    print("[3/17] brand summary previous")
    brand_summary_previous = client.geo_analysis("brand", ["visibility", "citation", "sentiment"], "summary", prev)

    print("[4/17] brand ranking current")
    brand_ranking_current = client.geo_analysis(
        "brand",
        ["visibility", "citation", "sentiment"],
        "ranking",
        period,
        ranking={"orderBy": "visibility", "direction": "desc"},
    )
    print("[5/17] brand ranking previous")
    brand_ranking_previous = client.geo_analysis(
        "brand",
        ["visibility", "citation", "sentiment"],
        "ranking",
        prev,
        ranking={"orderBy": "visibility", "direction": "desc"},
    )

    print("[6/17] brand trend 7d")
    brand_trend_7d = client.geo_analysis("brand", ["visibility", "citation", "sentiment"], "trend", period)

    period_30 = DateRange((datetime.strptime(period.end, "%Y-%m-%d") - timedelta(days=29)).strftime("%Y-%m-%d"), period.end)
    print("[7/17] brand trend 30d")
    brand_trend_30d = client.geo_analysis("brand", ["visibility", "citation", "sentiment"], "trend", period_30)

    print("[8/17] platform ranking")
    platform_ranking = client.geo_analysis(
        "platform",
        ["visibility", "citation"],
        "ranking",
        period,
        ranking={"orderBy": "visibility", "direction": "desc"},
    )

    print("[9/17] topics")
    topics = client.fetch_paged("topics", period, page_size=100, max_pages=max_pages_per_endpoint)
    print("[10/17] topic ranking")
    topic_ranking = client.geo_analysis(
        "topic",
        ["visibility", "sentiment", "citation"],
        "ranking",
        period,
        ranking={"orderBy": "visibility", "direction": "desc"},
    )
    print("[11/17] topic trend")
    topic_trend = client.geo_analysis("topic", ["visibility", "sentiment", "citation"], "trend", period)

    print("[12/17] prompts")
    prompts = client.fetch_paged("prompts", period, page_size=100, max_pages=max_pages_per_endpoint)
    print("[13/17] citation domains")
    citation_domains = client.fetch_paged("citations/domains", period, page_size=100, max_pages=max_pages_per_endpoint)
    print("[14/17] citation urls")
    citation_urls = client.fetch_paged("citations/urls", period, page_size=100, max_pages=max_pages_per_endpoint)
    print("[15/17] citation urls previous")
    citation_urls_previous = client.fetch_paged("citations/urls", prev, page_size=100, max_pages=max_pages_per_endpoint)

    print("[16/17] opportunities")
    content_opportunities = client.fetch_paged("opportunities/content", period, page_size=100, max_pages=max_pages_per_endpoint)
    backlink_opportunities = client.fetch_paged("opportunities/backlink", period, page_size=100, max_pages=max_pages_per_endpoint)
    community_opportunities = client.fetch_paged("opportunities/community", period, page_size=100, max_pages=max_pages_per_endpoint)

    prompt_items = extract_items(prompts)
    prompt_ids = [str(p.get("id")) for p in prompt_items if p.get("id")]
    if prompt_details_limit is not None:
        prompt_ids = prompt_ids[:prompt_details_limit]

    prompt_responses: Dict[str, Any] = {}
    prompt_query_fanout: Dict[str, Any] = {}
    prompt_citation_domains: Dict[str, Any] = {}
    prompt_citation_urls: Dict[str, Any] = {}

    print(f"[17/17] prompt detail endpoints for {len(prompt_ids)} prompts")
    for idx, pid in enumerate(prompt_ids, start=1):
        print(f"  - prompt {idx}/{len(prompt_ids)} id={pid}")
        prompt_responses[pid] = client.fetch_paged(f"prompts/{pid}/responses", period, page_size=100, max_pages=max_pages_per_endpoint)
        prompt_query_fanout[pid] = client.fetch_paged(f"prompts/{pid}/query_fanout", period, page_size=100, max_pages=max_pages_per_endpoint)
        prompt_citation_domains[pid] = client.fetch_paged(f"prompts/{pid}/citations/domains", period, page_size=100, max_pages=max_pages_per_endpoint)
        prompt_citation_urls[pid] = client.fetch_paged(f"prompts/{pid}/citations/urls", period, page_size=100, max_pages=max_pages_per_endpoint)

    return {
        "period": period,
        "previous_period": prev,
        "brand_info": brand_info,
        "brand_summary_current": brand_summary_current,
        "brand_summary_previous": brand_summary_previous,
        "brand_ranking_current": brand_ranking_current,
        "brand_ranking_previous": brand_ranking_previous,
        "brand_trend_7d": brand_trend_7d,
        "brand_trend_30d": brand_trend_30d,
        "platform_ranking": platform_ranking,
        "topics": topics,
        "topic_ranking": topic_ranking,
        "topic_trend": topic_trend,
        "prompts": prompts,
        "prompt_responses": prompt_responses,
        "prompt_query_fanout": prompt_query_fanout,
        "prompt_citation_domains": prompt_citation_domains,
        "prompt_citation_urls": prompt_citation_urls,
        "citation_domains": citation_domains,
        "citation_urls": citation_urls,
        "citation_urls_previous": citation_urls_previous,
        "content_opportunities": content_opportunities,
        "backlink_opportunities": backlink_opportunities,
        "community_opportunities": community_opportunities,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate premium GEO HTML report from real API data")
    parser.add_argument("--api_key", default=os.getenv("X_API_KEY"), help="Dageno API key or set X_API_KEY")
    parser.add_argument("--start_date", default=None, help="YYYY-MM-DD")
    parser.add_argument("--end_date", default=None, help="YYYY-MM-DD")
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(__file__), "..", "dist", "geo_weekly_report_premium_preview.html"),
        help="Output HTML path",
    )
    parser.add_argument(
        "--dump_json",
        default=os.path.join(os.path.dirname(__file__), "..", "dist", "geo_weekly_report_premium_data.json"),
        help="Output raw JSON path",
    )
    parser.add_argument(
        "--prompt_details_limit",
        type=int,
        default=-1,
        help="-1 means all prompts, otherwise fetch detail endpoints for first N prompts",
    )
    parser.add_argument(
        "--max_pages_per_endpoint",
        type=int,
        default=12,
        help="-1 means unlimited; otherwise cap each paginated endpoint to N pages for preview speed",
    )

    args = parser.parse_args()
    if not args.api_key:
        raise SystemExit("API key required. Pass --api_key or set X_API_KEY")

    if args.end_date and args.start_date:
        period = DateRange(args.start_date, args.end_date)
    else:
        end = datetime.now() - timedelta(days=1)
        start = end - timedelta(days=6)
        period = DateRange(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))

    client = DagenoClient(args.api_key)
    prompt_limit = None if args.prompt_details_limit < 0 else args.prompt_details_limit
    max_pages = None if args.max_pages_per_endpoint < 0 else args.max_pages_per_endpoint
    payload = fetch_all_data(client, period, prompt_limit, max_pages)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.dump_json)), exist_ok=True)

    with open(args.dump_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=lambda x: x.__dict__ if hasattr(x, "__dict__") else str(x))

    html_content = build_report_html(payload)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Report generated: {os.path.abspath(args.output)}")
    print(f"Raw data dump: {os.path.abspath(args.dump_json)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
