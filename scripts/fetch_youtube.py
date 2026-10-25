#!/usr/bin/env python3
"""
유튜브 채널 영상 목록 수집 — 공식 YouTube Data API v3.

    python3 scripts/fetch_youtube.py --handle @-180boss
    python3 scripts/fetch_youtube.py --queue

**왜 공식 API 만 쓰나.** 스크래핑(yt-dlp 등)은 유튜브 약관 위반 소지가 있고,
데이터센터 IP 는 대부분 차단된다(네이버 스마트스토어와 같은 문제). 공식 API 는
키만 있으면 Actions 러너에서도 안정적으로 돌고 쿼터도 넉넉하다.

**이 세션에서는 왜 못 도나.**
    www.youtube.com          → 프록시가 CONNECT 403 (허용목록 정책)
    www.googleapis.com       → ✅ 열려 있음 (키가 없어서 403 "unregistered callers")
즉 **API 키만 있으면 Actions 러너에서 바로 돈다.** 저장소 시크릿 `YOUTUBE_API_KEY`
를 등록하면 된다. 키가 없으면 조용히 건너뛴다(기존 자료 보존, 잡은 초록 유지)
— `scrapers/naver_openapi.py` 와 같은 규칙.

**자막은 이 API 로 못 받는다.** `captions.download` 는 **영상 소유자의 OAuth** 를
요구한다. 남의 채널 자막은 공식 경로로 받을 수 없다. 그래서 이 스크립트는
**메타데이터(제목·설명·공개일·길이·조회수)** 까지만 한다. 자막·본문이 필요하면
8장(README 하단)의 선택지를 본다.

**저작권.** 제목은 사실 정보지만 설명문은 채널 운영자의 저작물이다. 이 저장소는
공개이므로 설명문은 **발췌(기본 400자)** 만 저장하고 원문을 통째로 옮기지 않는다.
분석 결과는 우리가 쓴 요약으로 남기고 출처(영상 URL)를 단다.
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
OUT_DIR = ROOT / 'vault' / 'raw' / 'youtube'
API = 'https://www.googleapis.com/youtube/v3'
EXCERPT = 400          # 설명문 저장 상한 (저작권 — 통째로 옮기지 않는다)
PAGE = 50              # API 최대 페이지 크기
TIMEOUT = 40


class Quit(SystemExit):
    pass


def get(session, path: str, **params) -> dict:
    params['key'] = session.api_key
    r = session.get(f'{API}/{path}', params=params, timeout=TIMEOUT)
    if r.status_code == 403:
        body = r.text[:300]
        if 'quotaExceeded' in body:
            raise Quit('❌ API 일일 쿼터 소진 — 내일 다시 돌린다')
        raise Quit(f'❌ 403: {body}')
    r.raise_for_status()
    return r.json()


def resolve_channel(session, handle: str) -> dict:
    """핸들(@xxx) 또는 채널 ID → 채널 정보."""
    handle = handle.strip()
    if handle.startswith('UC') and len(handle) == 24:
        d = get(session, 'channels', part='snippet,contentDetails,statistics',
                id=handle)
    else:
        if not handle.startswith('@'):
            handle = '@' + handle
        d = get(session, 'channels', part='snippet,contentDetails,statistics',
                forHandle=handle)
    items = d.get('items') or []
    if not items:
        raise Quit(f'❌ 채널을 찾지 못했다: {handle}')
    return items[0]


def list_video_ids(session, uploads_playlist: str) -> list[str]:
    """업로드 재생목록을 끝까지 넘겨 **모든** 영상 id 를 모은다."""
    ids, token, page = [], None, 0
    while True:
        page += 1
        d = get(session, 'playlistItems', part='contentDetails',
                playlistId=uploads_playlist, maxResults=PAGE,
                **({'pageToken': token} if token else {}))
        for it in d.get('items', []):
            vid = (it.get('contentDetails') or {}).get('videoId')
            if vid:
                ids.append(vid)
        print(f'  목록 {page}쪽 — 누적 {len(ids)}개')
        token = d.get('nextPageToken')
        if not token:
            break
        time.sleep(0.2)
    return ids


ISO_DUR = re.compile(r'P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')


def dur_seconds(iso: str) -> int:
    m = ISO_DUR.fullmatch(iso or '')
    if not m:
        return 0
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + s


def hhmm(sec: int) -> str:
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'


def fetch_videos(session, ids: list[str]) -> list[dict]:
    out = []
    for i in range(0, len(ids), PAGE):
        chunk = ids[i:i + PAGE]
        d = get(session, 'videos', part='snippet,contentDetails,statistics',
                id=','.join(chunk))
        for it in d.get('items', []):
            sn, cd, st = it['snippet'], it.get('contentDetails', {}), it.get('statistics', {})
            desc = (sn.get('description') or '').strip()
            out.append({
                'id': it['id'],
                'url': f'https://www.youtube.com/watch?v={it["id"]}',
                'title': sn.get('title', ''),
                'published': (sn.get('publishedAt') or '')[:10],
                'duration_sec': dur_seconds(cd.get('duration', '')),
                'views': int(st.get('viewCount', 0) or 0),
                'likes': int(st.get('likeCount', 0) or 0),
                # 저작권 — 설명문은 발췌만. 원문 전체는 저장하지 않는다.
                'description_excerpt': desc[:EXCERPT],
                'description_truncated': len(desc) > EXCERPT,
                'tags': (sn.get('tags') or [])[:20],
            })
        print(f'  상세 {min(i + PAGE, len(ids))}/{len(ids)}개')
        time.sleep(0.2)
    return out


def slug(s: str) -> str:
    return re.sub(r'[^\w가-힣-]+', '-', s).strip('-').lower()[:50] or 'channel'


def write_index(ch: dict, vids: list[dict], d: pathlib.Path) -> None:
    sn, st = ch['snippet'], ch.get('statistics', {})
    total = sum(v['duration_sec'] for v in vids)
    by_year: dict[str, int] = {}
    for v in vids:
        by_year[v['published'][:4]] = by_year.get(v['published'][:4], 0) + 1

    lines = [
        f'# {sn.get("title", "")} — 영상 목록',
        '',
        '`scripts/fetch_youtube.py` 가 공식 YouTube Data API 로 자동 생성한다.',
        '**직접 고치지 말 것** — 다시 덮어쓴다. 분석·요약은 별도 문서에 쓴다.',
        '',
        f'- 채널: <{"https://www.youtube.com/channel/" + ch["id"]}>',
        f'- 수집일: {time.strftime("%Y-%m-%d")}',
        f'- 영상 **{len(vids)}개** · 총 길이 **{total // 3600}시간 {total % 3600 // 60}분**',
        f'- 구독자 {int(st.get("subscriberCount", 0) or 0):,} · '
        f'채널 총 조회 {int(st.get("viewCount", 0) or 0):,}',
        '',
        '> ⚠️ 설명문은 저작권 때문에 **발췌만** 저장한다(원문 전체 아님). '
        '내용을 보려면 영상 링크로 간다.',
        '',
        '## 연도별',
        '',
        '| 연도 | 영상 수 |',
        '|---|---|',
    ]
    for y in sorted(by_year, reverse=True):
        lines.append(f'| {y} | {by_year[y]} |')

    lines += ['', '## 전체 목록 (최신순)', '',
              '| 공개일 | 길이 | 조회 | 제목 |', '|---|---|---|---|']
    for v in sorted(vids, key=lambda x: x['published'], reverse=True):
        title = v['title'].replace('|', '\\|')
        lines.append(f'| {v["published"]} | {hhmm(v["duration_sec"])} | '
                     f'{v["views"]:,} | [{title}]({v["url"]}) |')

    (d / '_목록.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def fetch_channel(session, handle: str) -> int:
    ch = resolve_channel(session, handle)
    sn = ch['snippet']
    print(f'\n📺 {sn.get("title")}  ({ch["id"]})')

    uploads = ch['contentDetails']['relatedPlaylists']['uploads']
    ids = list_video_ids(session, uploads)
    print(f'  영상 {len(ids)}개 발견 — 상세 조회')
    vids = fetch_videos(session, ids)

    d = OUT_DIR / slug(sn.get('title', handle))
    d.mkdir(parents=True, exist_ok=True)
    (d / 'channel.json').write_text(json.dumps({
        'id': ch['id'],
        'title': sn.get('title', ''),
        'handle': handle,
        'published': (sn.get('publishedAt') or '')[:10],
        'description_excerpt': (sn.get('description') or '')[:EXCERPT],
        'statistics': ch.get('statistics', {}),
        'fetched_at': time.strftime('%Y-%m-%d'),
        'video_count': len(vids),
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    (d / 'videos.json').write_text(
        json.dumps(vids, ensure_ascii=False, indent=2), encoding='utf-8')
    write_index(ch, vids, d)
    print(f'  ✅ {d.relative_to(ROOT)} — 영상 {len(vids)}개')
    return len(vids)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--handle', action='append', default=[],
                    help='@핸들 또는 UC... 채널 ID (여러 번 가능)')
    a = ap.parse_args()

    key = os.environ.get('YOUTUBE_API_KEY', '').strip()
    if not key:
        # 네이버 오픈API 와 같은 규칙: 키가 없으면 조용히 건너뛴다.
        # 잡을 빨갛게 만들지 않는다 — 키는 사람이 등록해야 하는 것이고,
        # 그때까지 다른 수집이 멈출 이유가 없다.
        print('⏭️  YOUTUBE_API_KEY 가 없어 건너뜁니다.')
        print('   저장소 Settings → Secrets and variables → Actions 에')
        print('   YOUTUBE_API_KEY 를 등록하면 자동으로 수집합니다.')
        print('   (Google Cloud Console → YouTube Data API v3 → API 키)')
        return 0

    if not a.handle:
        print('--handle 을 하나 이상 주세요.')
        return 0

    session = requests.Session()
    session.api_key = key                      # type: ignore[attr-defined]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    for h in a.handle:
        try:
            total += fetch_channel(session, h)
        except Quit as e:
            print(e)
            return 1
        except requests.RequestException as e:
            print(f'❌ {h}: {type(e).__name__} {e}')
            return 1
    print(f'\n완료: 영상 {total}개')
    return 0 if total else 1


if __name__ == '__main__':
    sys.exit(main())
