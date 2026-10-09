#!/usr/bin/env python3
"""
계보도(lineage) SVG 생성기.

    python3 scripts/make_lineage_svg.py            # 전체 다시 그리기
    python3 scripts/make_lineage_svg.py 종관계도   # 하나만

SVG 를 손으로 찍지 않고 **노드·엣지 선언**에서 만든다. 상자 하나 옮기려고 좌표
수십 개를 고치는 일이 없도록, 그리고 다음 주제(가공방식 계통도 등)도 같은 틀로
찍어내려고 이렇게 둔다.

출력: vault/assets/*.svg — build_pdf.py 가 마크다운의 ![](assets/x.svg) 를
      인라인으로 박아 PDF 에 벡터로 들어간다(확대해도 안 깨진다).

엣지는 ㄱ자(elbow)로 돈다. 한 부모에서 갈라지는 자식들은 같은 x 에서 출발하므로
세로 줄기를 공유해 족보 특유의 괄호 모양이 자연히 나온다.
"""
import pathlib
import xml.etree.ElementTree as ET
import sys
import xml.sax.saxutils as sx

OUT_DIR = pathlib.Path(__file__).resolve().parent.parent / 'vault' / 'assets'

# 계통별 색 — 본문 설명과 색을 맞춘다(범례도 같은 값을 쓴다).
PALETTE = {
    'origin':  ('#4b5563', '#eef0f2'),   # 기원·야생
    'eth':     ('#15803d', '#eaf5ee'),   # 에티오피아 재래종
    'typica':  ('#1d4ed8', '#e9eefb'),   # 티피카 계통
    'bourbon': ('#b45309', '#fbf0e3'),   # 부르봉 계통
    'cross':   ('#7c3aed', '#f1ebfd'),   # 아라비카끼리 교잡
    'robusta': ('#be185d', '#fcebf2'),   # 로부스타·이입
    'f1':      ('#0d9488', '#e6f5f3'),   # F1 하이브리드
    'kenya':   ('#0369a1', '#e8f2f9'),   # 케냐 선발·육종
    'note':    ('#6b7280', '#f6f7f8'),   # 주석(점선)
}

FONT = '"Noto Sans KR","NanumGothic",sans-serif'
LINE_H = 17          # 상자 안 줄간격
PAD_Y = 12           # 상자 위아래 여백


class Node:
    def __init__(self, nid, x, y, w, lines, group='origin', dashed=False,
                 title_size=13, body_size=11):
        self.id, self.x, self.y, self.w = nid, x, y, w
        self.lines = lines                    # [제목, 설명1, 설명2 ...]
        self.group, self.dashed = group, dashed
        self.ts, self.bs = title_size, body_size
        self.h = PAD_Y * 2 + 2 + len(lines) * LINE_H

    @property
    def cx(self): return self.x + self.w / 2

    @property
    def cy(self): return self.y + self.h / 2

    @property
    def right(self): return self.x + self.w

    @property
    def bottom(self): return self.y + self.h

    def svg(self) -> str:
        stroke, fill = PALETTE[self.group]
        dash = ' stroke-dasharray="5 3"' if self.dashed else ''
        out = [f'<rect x="{self.x}" y="{self.y}" width="{self.w}" height="{self.h}" '
               f'rx="5" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{dash}/>',
               f'<rect x="{self.x}" y="{self.y}" width="4" height="{self.h}" '
               f'rx="2" fill="{stroke}"/>']
        ty = self.y + PAD_Y + 11
        for i, ln in enumerate(self.lines):
            if i == 0:
                out.append(f'<text x="{self.x + 12}" y="{ty}" font-family={FONT!r} '
                           f'font-size="{self.ts}" font-weight="700" fill="#17202a">'
                           f'{sx.escape(ln)}</text>')
            else:
                out.append(f'<text x="{self.x + 12}" y="{ty}" font-family={FONT!r} '
                           f'font-size="{self.bs}" fill="#4a5258">{sx.escape(ln)}</text>')
            ty += LINE_H
        return '\n'.join(out)


class Edge:
    """a → b. side='r' 오른쪽에서 나가 왼쪽으로, 'b' 아래로 나가 위로."""
    def __init__(self, a, b, label='', dashed=False, mx=None, side='r',
                 color='#9aa3aa'):
        self.a, self.b, self.label = a, b, label
        self.dashed, self.mx, self.side, self.color = dashed, mx, side, color

    def svg(self, nodes) -> str:
        a, b = nodes[self.a], nodes[self.b]
        dash = ' stroke-dasharray="4 3"' if self.dashed else ''
        if self.side == 'r':
            x1, y1 = a.right, a.cy
            x2, y2 = b.x, b.cy
            mx = self.mx if self.mx is not None else x1 + (x2 - x1) / 2
            d = f'M {x1} {y1} H {mx} V {y2} H {x2 - 7}'
            lx, ly = mx + 5, (y1 + y2) / 2 - 4
        else:                                   # 아래로
            x1, y1 = a.cx, a.bottom
            x2, y2 = b.cx, b.y
            my = self.mx if self.mx is not None else y1 + (y2 - y1) / 2
            d = f'M {x1} {y1} V {my} H {x2} V {y2 - 7}'
            lx, ly = (x1 + x2) / 2 + 5, my - 5
        out = [f'<path d="{d}" fill="none" stroke="{self.color}" stroke-width="1.5" '
               f'stroke-linejoin="round" marker-end="url(#arw)"{dash}/>']
        if self.label:
            w = len(self.label) * 7.6 + 8
            out.append(f'<rect x="{lx - 3}" y="{ly - 10}" width="{w}" height="14" '
                       f'rx="3" fill="#ffffff" opacity="0.92"/>')
            out.append(f'<text x="{lx + 1}" y="{ly}" font-family={FONT!r} '
                       f'font-size="10.5" fill="#5b6166">{sx.escape(self.label)}</text>')
        return '\n'.join(out)


def band(x, y, w, h, text, color):
    """계통 묶음을 알려주는 옅은 배경 띠."""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{color}" '
            f'opacity="0.42"/>'
            f'<text x="{x + 13}" y="{y + 19}" font-family={FONT!r} font-size="12" '
            f'font-weight="800" fill="#7a848c" letter-spacing="1.2">'
            f'{sx.escape(text)}</text>')


def legend(x, y, items):
    out = []
    for i, (g, label) in enumerate(items):
        stroke, fill = PALETTE[g]
        cx = x + i * 182
        out.append(f'<rect x="{cx}" y="{y}" width="15" height="15" rx="3" '
                   f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
        out.append(f'<text x="{cx + 21}" y="{y + 12}" font-family={FONT!r} '
                   f'font-size="11.5" fill="#4a5258">{sx.escape(label)}</text>')
    return '\n'.join(out)


def wrap(w, h, title, sub, parts) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%">
<defs>
  <marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6"
          markerHeight="6" orient="auto-start-reverse">
    <path d="M 0 1 L 9 5 L 0 9 z" fill="#9aa3aa"/>
  </marker>
</defs>
<rect width="{w}" height="{h}" fill="#ffffff"/>
<text x="26" y="34" font-family={FONT!r} font-size="23" font-weight="800"
      fill="#17202a">{sx.escape(title)}</text>
<text x="26" y="56" font-family={FONT!r} font-size="12.5"
      fill="#6b7280">{sx.escape(sub)}</text>
{parts}
</svg>"""


def draw(nodes: list[Node], edges: list[Edge], extras: str) -> str:
    reg = {n.id: n for n in nodes}
    return ('\n'.join([extras]
                      + [e.svg(reg) for e in edges]
                      + [n.svg() for n in nodes]))


# ══════════════════════════ ① 종(species) 관계도 ══════════════════════════

def fig_species() -> tuple[str, str]:
    # 이 그림만 세로(본문) 페이지에 인라인으로 들어간다. 본문 폭이 178mm 뿐이라
    # 캔버스를 작게 잡아야 글자가 읽히는 크기로 인쇄된다(790 단위 ≈ 7pt).
    W, H = 790, 440
    N = [
        Node('eu', 10, 74, 232,
             ['Coffea eugenioides', '동아프리카 · 2배체(2n=22)', '카페인이 매우 낮다'],
             'origin'),
        Node('ca', 10, 194, 232,
             ['Coffea canephora (로부스타)', '2배체(2n=22) · 타가수분',
              '쓴맛·카페인 높고 병에 강하다'], 'robusta'),
        Node('ar', 288, 134, 232,
             ['Coffea arabica', '4배체(2n=44) · 자가수분', '두 종이 합쳐진 이질사배체',
              '약 35만~61만 년 전 단 한 번'], 'typica', title_size=14),
        Node('var', 558, 145, 222,
             ['아라비카 안의 품종(variety)', '티피카 · 부르봉 · 게이샤 · 카투라 …',
              '이 문서가 다루는 층이 여기다'], 'bourbon'),
        Node('out', 288, 306, 492,
             ['같은 속(Coffea)의 다른 종들',
              'C. liberica / C. excelsa — 극소수 재배 · '
              'C. stenophylla — 2018년 야생 재발견'], 'note', dashed=True),
    ]
    E = [
        Edge('eu', 'ar', '교배', mx=265),
        Edge('ca', 'ar', '', mx=265),
        Edge('ar', 'var', '품종 분화', mx=539),
    ]
    extras = (
        f'<text x="10" y="416" font-family={FONT!r} font-size="11.5" fill="#5b6166">'
        f'<tspan font-weight="700">“아라비카 · 로부스타”는 종(species) 이름</tspan>'
        f'<tspan>, </tspan>'
        f'<tspan font-weight="700">“게이샤 · 카투라”는 아라비카 안의 품종 이름</tspan>'
        f'<tspan>이다. 이 둘을 같은 층에 놓고 비교하면 계속 헷갈린다.</tspan></text>')
    return 'species.svg', wrap(
        W, H, '① 종(species) 관계도 — 아라비카는 어디서 왔나',
        '분류 층위: 속(Coffea) → 종(species) → 품종(variety)',
        draw(N, E, extras))


# ════════════════ ② 에티오피아 재래종 갈래 ════════════════
# 한 장에 다 넣으면 A4 가로로 줄였을 때 본문이 4pt 가 돼 못 읽는다(2026-10-09 실측).
# 인쇄 크기 = min(가로275mm/W, 세로168mm/H) 로 정해지므로, 글자를 키우려면
# 폰트가 아니라 **한 장에 담는 정보량**을 줄여야 한다. 그래서 네 장으로 쪼갰다.

def fig_eth() -> tuple[str, str]:
    W, H = 1180, 580
    C = [20, 230, 460, 700, 940]
    WID = 218
    N = [
        Node('wild', C[0], 200, 200,
             ['야생 아라비카', '에티오피아 남서부 숲', '수천 개 유전형'], 'origin'),
        Node('ethg', C[1], 180, WID,
             ['에티오피아 재래종', '예멘을 거치지 않은 갈래', '= 원래의 다양성'], 'eth'),
        Node('farm', C[2], 90, WID,
             ['쿠루메 · 데가 · 월리쇼', '농가가 생김새로 붙인 이름',
              '유전자 검사를 거치지 않았다'], 'eth'),
        Node('jarc', C[2], 182, WID,
             ['JARC 선발종', '74110 · 74112 · 74158', '앞 두 자리 74 = 채집 연도 1974'],
             'eth'),
        Node('gesha', C[2], 274, WID,
             ['게샤 Gesha', '1931년 게샤 숲 채집'], 'eth'),
        Node('wush', C[2], 349, WID,
             ['우슈우슈 Wush Wush', '카파 지역 재래종'], 'eth'),
        Node('catie', C[3], 266, WID,
             ['CATIE T2722', '코스타리카 등록 1953', '탄자니아를 거쳐 들어옴'], 'eth'),
        Node('panag', C[4], 257, 222,
             ['파나마 게이샤', '1963 도입 → 오래 방치',
              '2004 Best of Panama 로 폭발', '유전적으로 균일한 한 집단'], 'eth'),
        Node('core', C[2], 440, 700,
             ['DNA 로 뒤집힌 이름들 — "코어 에티오피아" 그룹',
              '핑크 부르봉 · 치로소 · 아지 · 시드라',
              '이름은 부르봉/카투라인데 유전자는 에티오피아 재래종이다 (2017·2023 검사)'],
             'note', dashed=True),
    ]
    E = [
        Edge('wild', 'ethg'),
        Edge('ethg', 'farm'), Edge('ethg', 'jarc'),
        Edge('ethg', 'gesha'), Edge('ethg', 'wush'),
        Edge('gesha', 'catie'), Edge('catie', 'panag'),
        Edge('ethg', 'core', dashed=True, mx=430),
    ]
    extras = legend(24, 548, [('origin', '기원'), ('eth', '에티오피아 재래종'),
                              ('note', 'DNA 로 재분류됨')])
    return 'lineage-eth.svg', wrap(
        W, H, '② 계보도 1 — 에티오피아 재래종 갈래',
        '예멘을 거치지 않은 쪽. 중남미 품종들과 유전적 거리가 가장 멀어서 향미가 튄다.',
        draw(N, E, extras))


# ════════════════ ③ 예멘 → 티피카 · 부르봉 본류 ════════════════

def fig_main() -> tuple[str, str]:
    W, H = 1190, 650
    C = [18, 215, 440, 692, 944]
    WID = 222
    N = [
        Node('yemen', C[0], 250, 190,
             ['예멘 재배', '15~16세기 전파', '여기서 소수만 밖으로'], 'origin'),
        Node('typ', C[1], 150, WID,
             ['티피카 Typica', '예멘→인도→자바(1699)', '→암스테르담(1706)→파리(1714)',
              '→마르티니크(1723)→중남미'], 'typica'),
        Node('bou', C[1], 300, WID,
             ['부르봉 Bourbon', '예멘→부르봉섬(레위니옹)', '1708·1715·1718 세 번 시도',
              '→19세기 중반 브라질로'], 'bourbon'),
        Node('mara', C[2], 96, WID,
             ['마라고지페 (1800년대·브라질)', '티피카 변이 — 생두가 가장 크다'], 'typica'),
        Node('pach', C[2], 168, WID,
             ['파체 (과테말라)', '티피카 변이 — 왜성'], 'typica'),
        Node('catu', C[2], 240, WID,
             ['카투라 (1937·브라질)', '부르봉 변이 — 왜성',
              '밀식이 가능해졌다 = 산업이 바뀜'], 'bourbon'),
        Node('paca', C[2], 329, WID,
             ['파카스 (1949·엘살바도르)', '부르봉 변이 — 왜성'], 'bourbon'),
        Node('vill', C[2], 401, WID,
             ['비야사치 (1950~60년대·코스타리카)', '부르봉 변이 — 왜성'], 'bourbon'),
        Node('laur', C[2], 473, WID,
             ['라우리나 / 부르봉 포인투', '레위니옹 변이 — 카페인 약 절반'], 'bourbon'),
        Node('mund', C[3], 120, WID,
             ['문도노보 (1943·브라질)', '티피카 × 부르봉 자연 교잡',
              '키 크고 수확량 많다'], 'cross'),
        Node('cata', C[3], 216, WID,
             ['카투아이', '문도노보 × 카투라 (IAC)',
              '문도노보의 힘 + 카투라의 왜성'], 'cross'),
        Node('pacm', C[3], 312, WID,
             ['파카마라 (1958·엘살바도르)', '파카스 × 마라고지페',
              '생두가 크고 향미가 튄다'], 'cross'),
        Node('sl28', C[4], 420, WID,
             ['SL28 (1935·케냐)', '부르봉 계열로 판정 · 케냐 컵의 원형',
              '내건성↑ 수확량↓ 내병성↓'], 'kenya'),
        Node('sl34', C[4], 516, WID,
             ['SL34 (1930년대·케냐)', '"프렌치미션" 라벨 탓에 부르봉으로 오해',
              '유전자는 티피카 계열'], 'kenya'),
    ]
    E = [
        Edge('yemen', 'typ', mx=400), Edge('yemen', 'bou', mx=400),
        Edge('typ', 'mara'), Edge('typ', 'pach'),
        Edge('bou', 'catu'), Edge('bou', 'paca'),
        Edge('bou', 'vill'), Edge('bou', 'laur'),
        Edge('typ', 'mund', mx=672), Edge('bou', 'mund', mx=680),
        Edge('mund', 'cata', side='b', mx=196),
        Edge('catu', 'cata', mx=676),
        Edge('paca', 'pacm', mx=666), Edge('mara', 'pacm', mx=684),
        Edge('bou', 'sl28', mx=924), Edge('typ', 'sl34', mx=916),
    ]
    extras = legend(22, 614, [('origin', '예멘'), ('typica', '티피카 계통'),
                              ('bourbon', '부르봉 계통'), ('cross', '아라비카끼리 교잡'),
                              ('kenya', '케냐 선발')])
    return 'lineage-main.svg', wrap(
        W, H, '③ 계보도 2 — 예멘을 거친 두 계통과 그 자손',
        '현대 재배 품종의 거의 전부가 여기 있다. 돌연변이는 한 나무에서 저절로 생긴 변종, '
        '교잡은 두 품종을 교배한 것.',
        draw(N, E, extras))


# ════════════════ ④ 티모르 하이브리드와 이입종 ════════════════

def fig_rust() -> tuple[str, str]:
    W, H = 1030, 540
    C = [18, 252, 502, 762]
    WID = 238
    N = [
        Node('rob', C[0], 110, 215,
             ['로부스타', 'Coffea canephora', '녹병·커피베리병에 강하다'], 'robusta'),
        Node('ara', C[0], 245, 215,
             ['아라비카', '맛은 좋은데 병에 약하다'], 'typica'),
        Node('th', C[1], 140, WID,
             ['티모르 하이브리드 (1927)', '티모르섬에서 발견된',
              '아라비카 × 로부스타 자연 교배종', '컵 품질은 두 종의 중간'], 'robusta'),
        Node('catu', C[1], 280, WID,
             ['카투라 (왜성)', '부르봉 돌연변이'], 'bourbon'),
        Node('vill', C[1], 352, WID,
             ['비야사치 (왜성)', '부르봉 돌연변이'], 'bourbon'),
        Node('tb', C[1], 424, WID,
             ['티피카 · 부르봉'], 'typica'),
        Node('cati', C[2], 130, WID,
             ['카티모르 계열', 'TH × 카투라',
              '저고도에서 나무맛·고무 뉘앙스 지적'], 'robusta'),
        Node('sarc', C[2], 250, WID,
             ['사치모르 계열', 'TH × 비야사치'], 'robusta'),
        Node('tabi', C[2], 345, WID,
             ['타비 (2002·콜롬비아)', 'TH × 티피카·부르봉'], 'robusta'),
        Node('colo', C[3], 86, WID,
             ['콜롬비아 (1982)', '세니카페 — 카티모르 1세대'], 'robusta'),
        Node('cast', C[3], 158, WID,
             ['카스티요 (2005)', '세니카페 — 23년 육종',
              '컵 품질 평가는 논쟁 중'], 'robusta'),
        Node('mars', C[3], 258, WID,
             ['마르셀레사', 'CIRAD·CATIE — 사치모르',
              'TH 832/2 × 비야사치 CIFC 971/10'], 'robusta'),
        Node('obat', C[3], 358, WID,
             ['오바타 · IAPAR59 · 투피', '브라질 사치모르 선발',
              '고고도에서 스페셜티 등급 보고'], 'robusta'),
    ]
    E = [
        Edge('rob', 'th', mx=238), Edge('ara', 'th', mx=244),
        Edge('th', 'cati', mx=482), Edge('catu', 'cati', mx=474),
        Edge('th', 'sarc', mx=490), Edge('vill', 'sarc', mx=482),
        Edge('th', 'tabi', mx=466), Edge('tb', 'tabi', mx=474),
        Edge('cati', 'colo'), Edge('cati', 'cast'),
        Edge('sarc', 'mars'), Edge('sarc', 'obat'),
    ]
    extras = legend(20, 500, [('robusta', '로부스타 유전자 이입'),
                              ('bourbon', '부르봉 계통'), ('typica', '아라비카 본류')])
    return 'lineage-rust.svg', wrap(
        W, H, '④ 계보도 3 — 로부스타 유전자가 들어온 길',
        '아라비카는 유전적 폭이 좁아 병 저항성을 종 안에서 못 찾았다. 그래서 밖에서 끌어왔다 '
        '— 대신 컵 품질을 내줬다.',
        draw(N, E, extras))


# ════════════════ ⑤ F1 하이브리드와 케냐 복합 육종 ════════════════

def fig_f1() -> tuple[str, str]:
    W, H = 1120, 500
    C = [18, 300, 580, 858]
    WID = 258
    N = [
        Node('sarc', C[0], 80, WID,
             ['사치모르 T5296', '티모르 하이브리드 × 비야사치', '→ 녹병 저항성 담당'],
             'robusta'),
        Node('rume', C[0], 190, WID,
             ['루메 수단 Rume Sudan', '1941년 남수단 보마고원 야생 채집',
              '좁은 아라비카 풀의 희귀한 외부 다양성'], 'origin'),
        Node('mars', C[0], 310, WID,
             ['마르셀레사', '사치모르 계열 순계'], 'robusta'),
        Node('cms', C[0], 390, WID,
             ['웅성불임 모계 (CIR-SM01)', '씨앗 번식을 가능하게 한 열쇠'], 'f1'),
        Node('h1', C[1], 120, WID,
             ['센트로아메리카노 (H1)', '사치모르 T5296 × 루메 수단',
              '수확량·품질 모두 높다', '뿌리가 얕아 바람·가뭄에 약함'], 'f1'),
        Node('star', C[1], 330, WID,
             ['스타마야 Starmaya', '웅성불임 모계 × 마르셀레사',
              '씨앗으로 대량 보급 가능한 첫 F1'], 'f1'),
        Node('ruiru', C[2], 110, WID,
             ['루이루 11 (1985)', '왜성·다수확·내병성',
              '부계에 K7 · SL28 · 루메 수단'], 'kenya'),
        Node('batian', C[2], 220, WID,
             ['바티안 (2010·KALRO)', '녹병·CBD 저항 + 품질 유지 목표',
              'SL28·SL34·루메수단·N39·K7·SL4·TH'], 'kenya'),
    ]
    E = [
        Edge('sarc', 'h1', mx=282), Edge('rume', 'h1', mx=276),
        Edge('mars', 'star', mx=288), Edge('cms', 'star', mx=282),
        Edge('rume', 'ruiru', mx=560), Edge('rume', 'batian', mx=552),
    ]
    extras = '\n'.join([
        f'<text x="580" y="420" font-family={FONT!r} font-size="11.5" fill="#5b6166">'
        f'F1 = 유전적으로 먼 두 부모의 1세대. 잡종강세로 수확량·기후 적응폭·내병성이 '
        f'한꺼번에 올라간다.</text>',
        f'<text x="580" y="440" font-family={FONT!r} font-size="11.5" fill="#5b6166">'
        f'육종 기간도 순계 25~30년 → 10~20년으로 짧다. 난점은 번식이었고, '
        f'스타마야가 그것을 풀었다.</text>',
        legend(20, 464, [('robusta', '이입 계열'), ('origin', '야생 수단'),
                         ('f1', 'F1 하이브리드'), ('kenya', '케냐 복합 육종')]),
    ])
    return 'lineage-f1.svg', wrap(
        W, H, '⑤ 계보도 4 — F1 하이브리드와 케냐 복합 육종',
        '지금 육종의 주류. 저항성 계열과 야생 다양성을 다시 교배해 수확량과 품질을 '
        '같이 잡으려는 시도.',
        draw(N, E, extras))


FIGS = {'종관계도': fig_species, '에티오피아갈래': fig_eth,
        '본류계보도': fig_main, '내병성계보도': fig_rust, 'F1계보도': fig_f1}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    want = sys.argv[1:] or list(FIGS)
    for key in want:
        if key not in FIGS:
            print(f'❌ 모르는 그림: {key} (가능: {", ".join(FIGS)})')
            return 2
        name, svg = FIGS[key]()
        # XML 파싱 검사 — SVG 가 깨지면 브라우저는 조용히 SVG 를 포기하고 전체를
        # 글자로 흘려버린다(에러가 안 난다). 그러면 PDF 에 그림 대신 텍스트 덩어리가
        # 들어간 채 그대로 나간다. 그래서 저장 전에 반드시 파싱해본다.
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            print(f'❌ {key}: SVG 가 올바른 XML 이 아니다 — {e}')
            print('   (<text> 안에 <b>·<br> 같은 HTML 태그를 넣지 않았는지 확인)')
            return 3
        (OUT_DIR / name).write_text(svg, encoding='utf-8')
        print(f'✅ {key} → vault/assets/{name} ({len(svg):,} bytes)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
