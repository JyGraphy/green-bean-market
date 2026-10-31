#!/bin/bash
# 루베르·아마티보(네이버 스마트스토어) 자동 수집을 macOS launchd 에 등록한다.
# 네이버가 데이터센터 IP 를 막으므로 이 수집은 '집 네트워크의 맥'에서만 된다.
# 등록하면 매일 정해진 시각에 맥이 자동으로 브라우저 수집→커밋→푸시한다.
#
# 사용:  bash scripts/install_smartstore_launchd_mac.sh          # 기본 06:20 등록
#        bash scripts/install_smartstore_launchd_mac.sh 7 30     # 07:30 으로
#        bash scripts/install_smartstore_launchd_mac.sh --uninstall
#
# ⚠️ 선행 조건(한 번만): playwright 설치 + (필요 시) 네이버 로그인 1회.
#     python3 -m pip install playwright && python3 -m playwright install chromium
#     python3 scripts/update_smartstore_browser_local.py   # 창에서 1회 로그인(필요할 때만)
set -e

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.greenbean.smartstore"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$REPO/.pw-smartstore.log"

if [ "$1" = "--uninstall" ]; then
  launchctl unload "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"
  echo "✅ 자동 실행 해제됨 ($PLIST 삭제)"
  exit 0
fi

HOUR="${1:-6}"
MIN="${2:-20}"
PYBIN="$(command -v python3)"

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-lc</string>
    <string>cd "$REPO" &amp;&amp; HEADLESS=1 "$PYBIN" scripts/update_smartstore_browser_local.py &gt;&gt; "$LOG" 2&gt;&amp;1</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>$HOUR</integer><key>Minute</key><integer>$MIN</integer></dict>
  <key>RunAtLoad</key><false/>
  <key>StandardErrorPath</key><string>$LOG</string>
  <key>StandardOutPath</key><string>$LOG</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
printf '✅ 등록 완료 — 매일 %02d:%02d 에 맥이 자동으로 루베르·아마티보를 수집·푸시합니다.\n' "$HOUR" "$MIN"
echo "   로그: $LOG"
echo "   지금 한 번 테스트:  launchctl start $LABEL  (그리고 tail -f \"$LOG\")"
echo "   해제:  bash scripts/install_smartstore_launchd_mac.sh --uninstall"
echo
echo "참고: 맥이 그 시각에 켜져 있어야 실행됩니다(잠자기면 깨어난 뒤 곧 실행)."
echo "      네이버 로그인 세션이 만료되면 수집이 0개가 될 수 있고, 그때만"
echo "      'python3 scripts/update_smartstore_browser_local.py' 를 창 모드로 1회 재로그인하면 됩니다."
