# Aillio Bullet R1 (v2 / R2 Pro)

- heat_source: 하이브리드 — 드럼 + 유도가열(IH), 가스/화염 아님
- temp_probe: BT+ET + 선택형 IBTS(적외선 표면센서, 열지연 없음)
- typical_total_time: 8–12분 (배치 약 400g–1.2kg)
- chart_app: RoasTime (Aillio 자체 앱)
- verified: no

## 판독 규칙

- Induction heating gives fast, precise power response — ROR reacts to power-level changes
  noticeably QUICKER than a gas-fired drum (Probat/Giesen/Fuji Royal), though still slower than
  IKAWA's fluid-bed.
- If an IBTS (Infrared Bean Temperature Sensor) curve is present, it reads bean SURFACE
  temperature with NO thermometric lag: it typically shows NO dip/turning-point after charge,
  and reads roughly 15–17°C (~30°F) HIGHER than the traditional contact bean probe at the same
  moment. Do NOT force an IBTS curve to show a turning point just because a classic BT curve
  normally has one — its absence is expected and CORRECT for IBTS, not a reading error.
- If BOTH a contact bean-probe curve and an IBTS curve are shown, they are NOT interchangeable —
  check the legend to see which is which. The contact-probe curve has the classic post-charge
  dip; the IBTS curve does not.
- RoasTime is Aillio's own app; no fixed color convention (e.g. Artisan's red=BT) is confirmed
  to carry over. Always read the on-image legend rather than assuming colors from memory.
- Batch size is small (400g–1.2kg) with a wide preheat range (160–310°C) — total roast time is
  typically 8–12 min; do not stretch it toward Probat-length 15–20 min ranges.
- Controls include 9 power levels, 12 fan speeds, 9 drum speeds. If a bottom control chart shows
  stepped lines, expect discrete integer levels (not smooth curves) — conceptually similar to
  Stronghold's step controls, but the channel names differ (power/fan/drum, not
  열풍/할로겐/드럼히터/교반) — do not reuse Stronghold's Korean labels for this machine.

## 근거

- [Aillio Bullet R1 Roaster V2 - Sweet Maria's](https://www.sweetmarias.com/roasting/drum-roasters/aillio-bullet-r1-roaster.html)
- [Bullet R1 V2 - shop.aillio.com](https://shop.aillio.com/products/bullet-r1-v2)
- [IBTS – Infrared Bean Temperature Sensor Module Set - aillio.com](https://aillio.com/?product=infrared-bean-temperature-sensor-kit)
- [The Start of Something…. Our New Infrared Bean Temperature… - Aillio Medium](https://aillio.medium.com/the-start-of-something-39aa01d08fa9)
- [IBTS vs Bean Probe Temp discrepancies - Roast World Community](https://community.roast.world/t/ibts-vs-bean-probe-temp-discrepancies/9710)
- [Roasting Glossary - docs.aillio.com](https://docs.aillio.com/glossary/)
- 검증 대기 — 실제 RoasTime 차트 이미지로 아직 테스트하지 못함
