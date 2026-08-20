# Loring (S15 Falcon / S35 Kestrel / S70 Peregrine)

- heat_source: 열풍(대류) — single burner heats inlet air, not the drum (smokeless afterburner)
- temp_probe: BT(빠른 ~1.5mm 프로브)+ET(배기)
- typical_total_time: 10–16분 (예: S15 배치 15kg). 대형기(S35/S70)도 배치만 커질 뿐 시간대는 유사
- chart_app: Cropster (Roasting Intelligence) / Loring 자체 제어 소프트웨어 ("Roast Architect")
- verified: no

## 판독 규칙

- Even though beans tumble in a rotating DRUM, the flame does NOT sit under the drum — it heats
  the inlet air, so heat transfer is closer to convection than a Probat/Giesen-style gas drum.
  Expect ROR to respond FASTER to burner changes than a pure conduction drum, though still
  slower than IKAWA (fluid-bed) or Aillio (induction).
- Built-in afterburner recirculates and combusts exhaust smoke ("smokeless roasting") — do not
  expect a visible smoke/exhaust spike near first crack the way some drum-roaster software
  annotates; the exhaust curve reflects recirculated air temperature, not raw smoke output.
- A "Roast Profile" in Loring's own software (Roast Architect) is a BT curve defined by
  time/temperature ANCHOR POINTS set before roasting. If a chart shows a smooth planned line
  alongside a jagged actual line, treat the planned line as a target/plan (similar to the
  PROFILE EDITOR handling for IKAWA) — do not merge it into the actual bt_curve.
- Batch sizes are LARGE commercial scale (S15=15kg, S35=35kg, S70=70kg) yet total roast time is
  still 10–16 min thanks to strong airflow — do not assume a bigger batch means a much longer
  roast the way it would on a plain conduction drum.
- No fixed native color scheme is confirmed — charts are frequently exported through Cropster
  (which has its own conventions), not a Loring-branded skin. Always read the on-image legend.
- Loring's own bean probe is confirmed to be a very thin ~1.5mm thermocouple (vs. ~3mm on many
  classic drum roasters, e.g. Diedrich), per Loring's own thermocouple parts listing. Roasters
  comparing machines report this fast probe produces a noticeably TALLER/SHARPER RoR peak right
  at the turning point, a FLATTER-looking RoR through the middle-to-end of the roast, and a
  HIGHER absolute end-of-roast BT reading for the same visual roast color than a slower probe
  would show (one documented comparison: ~415°F on Loring vs ~399–401°F on a Diedrich for a
  similar color). When judging "how developed" a Loring BT curve looks near the end, do not
  assume the same BT-to-color mapping as a classic drum roaster — a higher absolute BT number can
  still be a comparable roast level, not necessarily a hotter/more-developed roast.

## 근거

- [PID Coffee Roaster Explained - Loring Smart Roast](https://loring.com/pid-coffee-roaster-explained/)
- [Loring - Roasting Intelligence Setup - Cropster](https://help.cropster.com/en/knowledge/loring-roasting-intelligence-ri-setup)
- [Building a profile with Loring - Global Coffee Report](https://www.gcrmag.com/building-a-profile-with-loring/)
- [LoRing S15 FALCon Tech Data (PDF)](https://loring.com/wp-content/uploads/2015/11/Loring-S15_EN_Tech-data_1002695_revB.pdf)
- [Loring S70 Peregrine Data Sheet (PDF)](https://loring.com/wp-content/uploads/2018/11/Loring-S70-Peregrine-Data-Sheet.pdf)
- [My First Impressions Of The Loring S15 Coffee Roaster - Path Coffee Roasters](https://pathcoffees.com/loring-s15-coffee-roaster-first-impressions/)
- [Thermocouple – Loring (shop.loring.com, 1.5mm BT 확인)](https://shop.loring.com/collections/thermocouple)
- [How Hot for a Loring - home-barista.com (로스터 실측 비교, 신뢰도 중 — 개인 포럼 보고)](https://www.home-barista.com/roasting/how-hot-for-loring-t82576.html)
- 검증 대기 — 실제 Loring/Cropster 차트 이미지로 아직 테스트하지 못함
