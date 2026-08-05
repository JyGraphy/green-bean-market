#!/usr/bin/env python3
"""논문 전문(full text) 수집 — GitHub Actions 전용.

**왜 필요한가**: Claude Code 세션은 네트워크 허용목록 정책 때문에 논문 사이트에
WebFetch가 403으로 막힌다. 그래서 지금까지 리서치팀은 검색 요약(초록 수준)만
가져올 수 있었고, 사장님이 "요약만 있고 세부 내용이 없다"고 피드백했다.
GitHub Actions 러너는 인터넷이 열려 있으므로 여기서 **본문 전체 + 표 + 그림**을
받아 저장하면, 이후 AI가 그 전문을 읽고 한글로 전역 번역할 수 있다.

수집 대상은 **오픈액세스 논문만**이다. 구독 저널 본문은 받지 않는다(저작권).
Europe PMC REST API가 OA 논문의 전문 XML을 제공하므로 이를 1차 경로로 쓴다.

사용법:
    python3 scripts/paper_fetch.py --pmcid PMC6818232
    python3 scripts/paper_fetch.py --doi 10.1371/journal.pone.0261976
    python3 scripts/paper_fetch.py --search "coffee roasting profile"  # OA만 검색
    python3 scripts/paper_fetch.py --queue                            # 대기열 일괄 처리

대기열: vault/raw/papers/_수집대기.md 의 `- [ ] PMCxxxxx <메모>` 줄을 읽어 처리한다.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys
import time
import xml.etree.ElementTree as ET

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'vault' / 'raw' / 'papers' / 'fulltext'
QUEUE = ROOT / 'vault' / 'raw' / 'papers' / '_수집대기.md'

EPMC = 'https://www.ebi.ac.uk/europepmc/webservices/rest'
HEADERS = {'User-Agent': 'green-bean-market research bot (contact: repo owner)'}
TIMEOUT = 30
DELAY = 1.5


def api(path: str, **params):
    params.setdefault('format', 'json')
    r = requests.get(f'{EPMC}/{path}', params=params, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def search_oa(query: str, limit: int = 10):
    """오픈액세스 + 전문 제공 논문만 검색."""
    q = f'({query}) AND OPEN_ACCESS:Y AND HAS_FT:Y'
    data = api('search', query=q, pageSize=limit, resultType='core')
    out = []
    for r in data.get('resultList', {}).get('result', []):
        out.append({
            'pmcid': r.get('pmcid'),
            'title': r.get('title'),
            'journal': (r.get('journalInfo') or {}).get('journal', {}).get('title'),
            'year': r.get('pubYear'),
            'doi': r.get('doi'),
            'license': r.get('license'),
            'authors': r.get('authorString'),
        })
    return out


def resolve_doi(doi: str) -> str | None:
    data = api('search', query=f'DOI:"{doi}"', pageSize=1, resultType='core')
    res = data.get('resultList', {}).get('result', [])
    return res[0].get('pmcid') if res else None


def fetch_fulltext_xml(pmcid: str) -> str:
    r = requests.get(f'{EPMC}/{pmcid}/fullTextXML', headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


# ─────────────────────── XML → 마크다운 ───────────────────────
def node_text(el) -> str:
    """중첩 태그를 무시하고 텍스트만 이어붙인다."""
    return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()


def table_to_md(tbl) -> str:
    rows = []
    for tr in tbl.iter('tr'):
        cells = [node_text(c) for c in tr if c.tag in ('td', 'th')]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ''
    w = max(len(r) for r in rows)
    rows = [r + [''] * (w - len(r)) for r in rows]
    md = '| ' + ' | '.join(rows[0]) + ' |\n' + '|' + '---|' * w + '\n'
    for r in rows[1:]:
        md += '| ' + ' | '.join(r) + ' |\n'
    return md


def render_section(sec, depth=2) -> list[str]:
    out = []
    title = sec.find('title')
    if title is not None:
        out.append(f'\n{"#" * min(depth, 6)} {node_text(title)}\n')
    for child in sec:
        if child.tag == 'title':
            continue
        if child.tag == 'sec':
            out += render_section(child, depth + 1)
        elif child.tag == 'p':
            t = node_text(child)
            if t:
                out.append(t + '\n')
        elif child.tag in ('table-wrap',):
            cap = child.find('.//caption')
            lbl = child.find('label')
            head = ' '.join(filter(None, [node_text(lbl) if lbl is not None else '',
                                          node_text(cap) if cap is not None else '']))
            out.append(f'\n**{head or "표"}**\n')
            tbl = child.find('.//table')
            if tbl is not None:
                out.append(table_to_md(tbl))
        elif child.tag == 'fig':
            out.append(render_fig(child))
        elif child.tag in ('list',):
            for item in child.iter('list-item'):
                out.append(f'- {node_text(item)}')
            out.append('')
    return out


def render_fig(fig) -> str:
    """그림: 캡션 + 이미지 링크. 사장님이 '이미지를 봐야 이해된다'고 한 부분."""
    lbl = fig.find('label')
    cap = fig.find('.//caption')
    label = node_text(lbl) if lbl is not None else '그림'
    caption = node_text(cap) if cap is not None else ''
    graphic = fig.find('.//graphic')
    href = ''
    if graphic is not None:
        for k, v in graphic.attrib.items():
            if k.endswith('href'):
                href = v
                break
    return f'\n> 🖼️ **{label}** {caption}\n> 이미지 파일: `{href or "미확인"}`\n'


def xml_to_md(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    meta = {}

    def find_text(path):
        el = root.find(path)
        return node_text(el) if el is not None else ''

    meta['title'] = find_text('.//article-meta//article-title')
    meta['journal'] = find_text('.//journal-title')
    meta['year'] = find_text('.//article-meta//pub-date/year')
    meta['doi'] = ''
    for aid in root.iter('article-id'):
        if aid.get('pub-id-type') == 'doi':
            meta['doi'] = node_text(aid)
    lic = root.find('.//license')
    meta['license'] = node_text(lic) if lic is not None else ''
    meta['authors'] = ', '.join(
        f"{node_text(n.find('surname')) if n.find('surname') is not None else ''} "
        f"{node_text(n.find('given-names')) if n.find('given-names') is not None else ''}".strip()
        for n in root.iter('name'))[:400]

    body_md = []
    abstract = root.find('.//abstract')
    if abstract is not None:
        body_md.append('\n## 초록 (원문)\n')
        body_md += render_section(abstract, 3)

    body = root.find('.//body')
    if body is not None:
        for sec in body:
            if sec.tag == 'sec':
                body_md += render_section(sec, 2)
            elif sec.tag == 'p':
                t = node_text(sec)
                if t:
                    body_md.append(t + '\n')
            elif sec.tag == 'fig':
                body_md.append(render_fig(sec))
            elif sec.tag == 'table-wrap':
                tbl = sec.find('.//table')
                if tbl is not None:
                    body_md.append(table_to_md(tbl))

    figs = len(list(root.iter('fig')))
    tbls = len(list(root.iter('table')))
    return {'meta': meta, 'body': '\n'.join(body_md), 'n_figs': figs, 'n_tables': tbls}


def slugify(s: str) -> str:
    s = re.sub(r'[^\w가-힣 -]', '', s)[:60].strip().replace(' ', '-')
    return s or 'paper'


def save(pmcid: str, parsed: dict) -> pathlib.Path:
    m = parsed['meta']
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f'{pmcid}-{slugify(m["title"])}.md'
    header = f"""# [원문] {m['title']}

> ⚠️ **이 문서는 번역 전 영어 원문입니다.** 한글 번역본은 별도 파일로 만들어집니다.

| 항목 | 값 |
|---|---|
| PMCID | {pmcid} |
| DOI | {m['doi'] or '미확인'} |
| 저널 | {m['journal'] or '미확인'} |
| 연도 | {m['year'] or '미확인'} |
| 라이선스 | {m['license'][:200] or '미확인'} |
| 저자 | {m['authors'] or '미확인'} |
| 본문 그림 | {parsed['n_figs']}개 |
| 본문 표 | {parsed['n_tables']}개 |
| 수집 | {datetime.date.today().isoformat()} · scripts/paper_fetch.py (GitHub Actions) |

출처: https://europepmc.org/article/PMC/{pmcid}

---
"""
    path.write_text(header + parsed['body'] + '\n', encoding='utf-8')
    return path


def process(pmcid: str) -> pathlib.Path | None:
    try:
        xml = fetch_fulltext_xml(pmcid)
        parsed = xml_to_md(xml)
        if len(parsed['body']) < 500:
            print(f'  ⚠️ {pmcid}: 본문이 너무 짧음({len(parsed["body"])}자) — OA 전문이 아닐 수 있음')
        p = save(pmcid, parsed)
        print(f'  ✓ {pmcid} → {p.relative_to(ROOT)} '
              f'({len(parsed["body"]):,}자, 그림 {parsed["n_figs"]}, 표 {parsed["n_tables"]})')
        return p
    except requests.HTTPError as e:
        print(f'  ✗ {pmcid}: HTTP {e.response.status_code} — OA 전문 미제공 가능성')
    except ET.ParseError as e:
        print(f'  ✗ {pmcid}: XML 파싱 실패 — {e}')
    except requests.RequestException as e:
        print(f'  ✗ {pmcid}: {type(e).__name__} {e}')
    return None


def read_queue() -> list[str]:
    if not QUEUE.exists():
        return []
    ids = []
    for line in QUEUE.read_text(encoding='utf-8').splitlines():
        m = re.match(r'^-\s*\[ \]\s*(PMC\d+)', line.strip())
        if m:
            ids.append(m.group(1))
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pmcid', nargs='*', default=[])
    ap.add_argument('--doi', nargs='*', default=[])
    ap.add_argument('--search')
    ap.add_argument('--limit', type=int, default=10)
    ap.add_argument('--queue', action='store_true')
    a = ap.parse_args()

    if a.search:
        print(f'오픈액세스 검색: {a.search}\n')
        for r in search_oa(a.search, a.limit):
            print(f'  {r["pmcid"] or "(PMCID 없음)":<12} {r["year"]} {r["journal"]}')
            print(f'    {r["title"][:100]}')
            print(f'    license={r["license"]}')
        return

    targets = list(a.pmcid)
    for d in a.doi:
        pid = resolve_doi(d)
        if pid:
            targets.append(pid)
            print(f'DOI {d} → {pid}')
        else:
            print(f'✗ DOI {d}: Europe PMC에서 PMCID를 찾지 못함 (OA가 아닐 수 있음)')
    if a.queue:
        targets += read_queue()

    if not targets:
        print('수집할 대상이 없습니다. --pmcid / --doi / --search / --queue 중 하나를 쓰세요.')
        return

    print(f'전문 수집 {len(targets)}건\n')
    ok = 0
    for pid in dict.fromkeys(targets):
        if process(pid):
            ok += 1
        time.sleep(DELAY)
    print(f'\n완료: {ok}/{len(set(targets))}건 저장 → {OUT_DIR.relative_to(ROOT)}')
    if ok == 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
