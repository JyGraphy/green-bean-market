"""
데이터 무결성 검증 게이트 (커밋 직전 최종 방어선)

스크래핑 결과(워킹트리 data/products.json)를 직전 커밋(git HEAD)과 비교해
다음을 검사한다. 하나라도 실패하면 종료코드 1 → 워크플로가 커밋을 차단한다.

  1. 스키마: 필수 필드 존재 / 타입 / price > 0
  2. 중복 ID 없음
  3. HEAD에 있던 store가 통째로 사라지지 않음
  4. store별 상품 수가 0 또는 기존 대비 50% 미만으로 급감하지 않음
  5. 전체 상품 수가 기존 대비 70% 미만으로 급감하지 않음
  6. 파생 파일(products_web.json) 개수가 products.json과 일치

의도적인 대량 변경(상점 정리 등) 시에는 환경변수 FORCE_DATA_UPDATE=1 로 4·5번
급감 검사만 건너뛸 수 있다. (스키마·중복·파일 일치 검사는 항상 수행)

이 스크립트는 run_all.py의 개별 스크래퍼 가드와 독립적으로 동작하므로,
미래에 새 스크래퍼가 가드를 우회하더라도 망가진 데이터의 커밋을 막는다.
"""
import json, os, sys, subprocess
from collections import Counter

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_FILE = os.path.join(ROOT, 'data', 'products.json')
WEB_FILE  = os.path.join(ROOT, 'data', 'products_web.json')

STORE_DROP_RATIO = 0.5   # store별: 기존 대비 이 비율 미만이면 실패
TOTAL_DROP_RATIO = 0.7   # 전체: 기존 대비 이 비율 미만이면 실패
REQUIRED_FIELDS  = ['id', 'store', 'name', 'price', 'origin', 'region', 'url']

FORCE = os.environ.get('FORCE_DATA_UPDATE') == '1'

errors = []   # 치명적 — 커밋 차단
warns  = []   # 경고 — 통과시키되 로그 기록


def load_current():
    with open(JSON_FILE, encoding='utf-8') as f:
        return json.load(f)['products']


def load_head():
    """직전 커밋의 products.json. 비교 불가(최초 커밋 등) 시 None."""
    try:
        out = subprocess.run(
            ['git', 'show', 'HEAD:data/products.json'],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        return json.loads(out.stdout)['products']
    except Exception as e:
        print(f"ℹ️  HEAD 비교 생략 (이전 데이터 없음/조회 실패: {e})")
        return None


def check_schema(products):
    ids = []
    for i, p in enumerate(products):
        for field in REQUIRED_FIELDS:
            if field not in p or p[field] in (None, ''):
                errors.append(f"스키마: {i}번째 상품에 '{field}' 누락/빈값 (store={p.get('store')}, name={p.get('name')})")
        price = p.get('price')
        if not isinstance(price, int) or isinstance(price, bool) or price <= 0:
            errors.append(f"가격 이상: id={p.get('id')} store={p.get('store')} name={p.get('name')} price={price!r}")
        if 'id' in p:
            ids.append(p['id'])

    dupes = [pid for pid, c in Counter(ids).items() if c > 1]
    if dupes:
        errors.append(f"중복 ID {len(dupes)}건: {sorted(dupes)[:20]}{' …' if len(dupes) > 20 else ''}")


def check_against_head(current, head):
    cur_by_store = Counter(p['store'] for p in current)
    head_by_store = Counter(p['store'] for p in head)

    # 3) store 통째 소멸
    for store, old_n in head_by_store.items():
        new_n = cur_by_store.get(store, 0)
        if new_n == 0 and old_n > 0:
            msg = f"store 소멸: '{store}' {old_n}개 → 0개"
            (warns if FORCE else errors).append(msg)

    # 4) store별 급감
    for store, old_n in head_by_store.items():
        new_n = cur_by_store.get(store, 0)
        if old_n >= 10 and 0 < new_n < old_n * STORE_DROP_RATIO:
            msg = f"store 급감: '{store}' {old_n}개 → {new_n}개 (기준 {STORE_DROP_RATIO:.0%} 미만)"
            (warns if FORCE else errors).append(msg)

    # 5) 전체 급감
    old_total, new_total = sum(head_by_store.values()), sum(cur_by_store.values())
    if old_total > 0 and new_total < old_total * TOTAL_DROP_RATIO:
        msg = f"전체 급감: {old_total}개 → {new_total}개 (기준 {TOTAL_DROP_RATIO:.0%} 미만)"
        (warns if FORCE else errors).append(msg)

    # 참고용 증감 리포트
    print("📊 store별 증감 (HEAD → 현재):")
    for store in sorted(set(head_by_store) | set(cur_by_store)):
        o, n = head_by_store.get(store, 0), cur_by_store.get(store, 0)
        flag = '' if o == n else ('  ⬆' if n > o else '  ⬇')
        print(f"   {o:4d} → {n:4d}  {store}{flag}")
    print(f"   {'─'*22}\n   {old_total:4d} → {new_total:4d}  합계")


def check_web_consistency(current):
    if not os.path.exists(WEB_FILE):
        errors.append("products_web.json 없음 — generate_sql.py 미실행?")
        return
    try:
        with open(WEB_FILE, encoding='utf-8') as f:
            web = json.load(f)
    except Exception as e:
        errors.append(f"products_web.json 파싱 실패: {e}")
        return
    if len(web) != len(current):
        errors.append(f"파생 파일 불일치: products.json {len(current)}개 vs products_web.json {len(web)}개")


def main():
    print("=" * 55)
    print("🔍 데이터 무결성 검증" + ("  (FORCE 모드: 급감 검사 경고로 강등)" if FORCE else ""))
    print("=" * 55)

    current = load_current()
    check_schema(current)

    head = load_head()
    if head is not None:
        check_against_head(current, head)

    check_web_consistency(current)

    if warns:
        print("\n⚠️  경고:")
        for w in warns:
            print(f"   - {w}")

    if errors:
        print("\n❌ 검증 실패 — 커밋 차단:")
        for e in errors:
            print(f"   - {e}")
        print("\n의도적 대량 변경이면 FORCE_DATA_UPDATE=1 로 재실행하세요.")
        sys.exit(1)

    print(f"\n✅ 검증 통과 — 상품 {len(current)}개, 무결성 이상 없음")
    sys.exit(0)


if __name__ == '__main__':
    main()
