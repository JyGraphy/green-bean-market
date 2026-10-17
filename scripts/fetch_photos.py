#!/usr/bin/env python3
"""
품종·로스팅 사진 수집기 — 위키미디어 공용(Wikimedia Commons)에서 **자유 라이선스** 사진만.

    python3 scripts/fetch_photos.py --queue        # 대기열 일괄
    python3 scripts/fetch_photos.py --key geisha --query "Coffea arabica Geisha"

Claude Code 세션은 네트워크 허용목록 정책으로 commons.wikimedia.org 가 403 이다
(2026-10-17 실측: 프록시가 CONNECT 를 거부). 그래서 이 스크립트는 **GitHub Actions
러너에서 돈다** — 논문·옥션 수집과 같은 구조다.

**왜 위키미디어만 쓰나.** 사진은 저작물이다. 구글 이미지에서 받아 문서에 넣으면
출처·라이선스가 없는 자료가 볼트에 섞인다. 위키미디어 공용은 파일마다 라이선스와
저작자가 API 로 같이 내려오므로, 자유 라이선스(CC0/PD/CC BY/CC BY-SA)만 통과시키고
저작자 표기를 자동으로 기록할 수 있다. ND(변형금지)·NC(비영리)·불명은 **버린다**.

저장물:
    vault/assets/photos/<키>-<n>.jpg     사진
    vault/raw/photos/<키>.json           파일별 출처·라이선스·저작자
    vault/raw/photos/_출처.md            사람이 읽는 저작자 표기 목록 (자동 생성)
"""
import argparse
import json
import os
import pathlib
import re
import sys
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / 'vault' / 'assets' / 'photos'
META_DIR = ROOT / 'vault' / 'raw' / 'photos'
QUEUE = META_DIR / '_수집대기.md'
CREDITS = META_DIR / '_출처.md'

API = 'https://commons.wikimedia.org/w/api.php'
# 위키미디어는 식별 가능한 User-Agent 를 요구한다(정책). 연락처 없이 보내면 차단될 수 있다.
UA = ('green-bean-market/1.0 (https://github.com/JyGraphy/green-bean-market; '
      'coffee variety reference) python-requests')
THUMB_W = 1000
DELAY = 1.0

# 통과시킬 라이선스. ND·NC 는 2차 문서(PDF)에 싣기 어렵고, 불명은 쓰지 않는다.
OK_LICENSE = re.compile(
    r'^(cc0|cc[- ]by(-sa)?([- ]\d(\.\d)?)?|public domain|pd-\w+|'
    r'attribution(-sharealike)?)', re.I)
BAD_LICENSE = re.compile(r'(\bnd\b|noderiv|non[- ]?commercial|\bnc\b|fair use)', re.I)


def strip_html(s: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s or '')).strip()


def search(session, query: str, limit: int) -> list[dict]:
    """Commons 에서 이미지 파일을 찾아 메타데이터까지 한 번에 받는다."""
    p = {
        'action': 'query', 'format': 'json', 'formatversion': 2,
        'generator': 'search', 'gsrsearch': f'filetype:bitmap {query}',
        'gsrnamespace': 6, 'gsrlimit': limit,
        'prop': 'imageinfo',
        'iiprop': 'url|size|extmetadata|mime',
        'iiurlwidth': THUMB_W,
    }
    r = session.get(API, params=p, timeout=40)
    r.raise_for_status()
    return r.json().get('query', {}).get('pages', []) or []


def usable(page: dict) -> tuple[bool, str, dict]:
    """자유 라이선스이고 쓸 만한 크기인지. (가능여부, 사유, 정보)."""
    ii = (page.get('imageinfo') or [{}])[0]
    if not ii:
        return False, '이미지 정보 없음', {}
    if not (ii.get('mime') or '').startswith('image/'):
        return False, f"이미지 아님({ii.get('mime')})", {}
    if (ii.get('width') or 0) < 500:
        return False, f"너무 작음({ii.get('width')}px)", {}

    em = ii.get('extmetadata') or {}
    lic = strip_html(em.get('LicenseShortName', {}).get('value', ''))
    info = {
        'title': page.get('title', ''),
        'license': lic,
        'license_url': strip_html(em.get('LicenseUrl', {}).get('value', '')),
        'author': strip_html(em.get('Artist', {}).get('value', '')) or '미상',
        'credit': strip_html(em.get('Credit', {}).get('value', '')),
        'description': strip_html(em.get('ImageDescription', {}).get('value', ''))[:400],
        'page_url': ii.get('descriptionurl', ''),
        'thumb_url': ii.get('thumburl') or ii.get('url', ''),
        'width': ii.get('width'), 'height': ii.get('height'),
    }
    if BAD_LICENSE.search(lic):
        return False, f'제한 라이선스({lic})', info
    if not OK_LICENSE.match(lic):
        return False, f'자유 라이선스로 확인 안 됨({lic or "표기 없음"})', info
    return True, '', info


def download(session, url: str, dest: pathlib.Path) -> bool:
    try:
        r = session.get(url, timeout=60)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f'    ✗ 내려받기 실패: {type(e).__name__} {e}')
        return False
    if len(r.content) < 8000:
        print(f'    ✗ 내려받은 파일이 너무 작다({len(r.content)}B)')
        return False
    dest.write_bytes(r.content)
    return True


def fetch_one(session, key: str, query: str, want: int, note: str = '') -> int:
    print(f'\n[{key}] "{query}" — {want}장 목표')
    try:
        pages = search(session, query, want * 4)
    except requests.RequestException as e:
        print(f'  ✗ 검색 실패: {type(e).__name__} {e}')
        return 0

    saved, records = 0, []
    for page in pages:
        if saved >= want:
            break
        ok, why, info = usable(page)
        if not ok:
            print(f'  – 건너뜀: {page.get("title","?")[:60]} — {why}')
            continue
        dest = IMG_DIR / f'{key}-{saved + 1}.jpg'
        if not download(session, info['thumb_url'], dest):
            continue
        info['file'] = f'vault/assets/photos/{dest.name}'
        info['bytes'] = dest.stat().st_size
        records.append(info)
        saved += 1
        print(f'  ✓ {dest.name}  {info["license"]}  — {info["title"][:60]}')
        time.sleep(DELAY)

    if records:
        (META_DIR / f'{key}.json').write_text(
            json.dumps({'key': key, 'query': query, 'note': note,
                        'fetched_at': time.strftime('%Y-%m-%d'),
                        'images': records}, ensure_ascii=False, indent=2),
            encoding='utf-8')
    if saved < want:
        print(f'  ⚠️ {saved}/{want}장만 확보 — 자유 라이선스 사진이 부족하다')
    return saved


QLINE = re.compile(r'^-\s*\[( |x|X)\]\s*(\S+)\s*\|\s*([^|]+?)\s*(?:\|\s*(.*))?$')


def read_queue() -> list[tuple[str, str, str]]:
    if not QUEUE.exists():
        return []
    out = []
    for line in QUEUE.read_text(encoding='utf-8').splitlines():
        m = QLINE.match(line.strip())
        if m and m.group(1) == ' ':
            out.append((m.group(2), m.group(3), (m.group(4) or '').strip()))
    return out


def mark_done(done: set[str]) -> None:
    """성공한 항목만 체크한다 — 실패는 남겨 다음 주에 다시 시도한다."""
    if not done or not QUEUE.exists():
        return
    today = time.strftime('%Y-%m-%d')
    out, n = [], 0
    for line in QUEUE.read_text(encoding='utf-8').splitlines():
        m = QLINE.match(line.strip())
        if m and m.group(1) == ' ' and m.group(2) in done:
            out.append(re.sub(r'^(-\s*)\[ \]', r'\1[x]', line) + f'  ✅ {today}')
            n += 1
        else:
            out.append(line)
    QUEUE.write_text('\n'.join(out).rstrip() + '\n', encoding='utf-8')
    print(f'\n📋 대기열 {n}건 완료 표시')


def write_credits() -> None:
    """저작자 표기 목록 — 라이선스 의무이자, 어떤 사진이 있는지 보는 목록."""
    rows = []
    for jf in sorted(META_DIR.glob('*.json')):
        d = json.loads(jf.read_text(encoding='utf-8'))
        for im in d.get('images', []):
            rows.append((d['key'], im))
    if not rows:
        return
    lines = [
        '# 사진 출처·저작자 표기',
        '',
        '`scripts/fetch_photos.py` 가 자동 생성한다. **직접 고치지 말 것** — 다시 덮어쓴다.',
        '',
        '위키미디어 공용(Wikimedia Commons)에서 **자유 라이선스**(CC0/PD/CC BY/CC BY-SA)인',
        '사진만 받는다. ND·NC·라이선스 불명은 수집 단계에서 버린다.',
        'CC BY-SA 사진을 쓴 문서는 같은 조건으로 공유해야 한다.',
        '',
        f'**총 {len(rows)}장**',
        '',
        '| 키 | 파일 | 라이선스 | 저작자 | 원본 |',
        '|---|---|---|---|---|',
    ]
    for key, im in rows:
        author = (im['author'] or '미상')[:60]
        lines.append(f'| {key} | `{pathlib.Path(im["file"]).name}` | {im["license"]} | '
                     f'{author} | [Commons]({im["page_url"]}) |')
    CREDITS.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'📝 {CREDITS.relative_to(ROOT)} 갱신 ({len(rows)}장)')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--queue', action='store_true')
    ap.add_argument('--key')
    ap.add_argument('--query')
    ap.add_argument('--count', type=int, default=2)
    a = ap.parse_args()

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)

    jobs: list[tuple[str, str, str]] = []
    if a.key and a.query:
        jobs.append((a.key, a.query, ''))
    if a.queue:
        jobs += read_queue()
    if not jobs:
        print('할 일이 없다. --queue 또는 --key/--query 를 쓰세요.')
        return 0

    session = requests.Session()
    session.headers.update({'User-Agent': UA})

    done, total = set(), 0
    for key, query, note in jobs:
        n = fetch_one(session, key, query, a.count, note)
        total += n
        if n:
            done.add(key)
    mark_done(done)
    write_credits()

    print(f'\n완료: {total}장 저장 → vault/assets/photos/')
    # 한 장도 못 받으면 잡을 빨갛게 — 조용히 빈손으로 끝나는 것을 막는다.
    return 0 if total else 1


if __name__ == '__main__':
    sys.exit(main())
