#!/bin/bash
# 23.11.2026 панель статистики (свой «Metricool»): ежедневный сбор в 08:10 Екб, страница на сайте по секретной ссылке. Режимы: vkl | itog | otkat
set -u
case "${1:-vkl}" in
vkl)
  mkdir -p /opt/klon /var/lib/gonets/stat /opt/stack/vitrina/v; install -m 644 /tmp/stat_panel.py /opt/klon/stat_panel.py; install -m 644 /tmp/panel_stil.py /opt/klon/panel_stil.py; install -m 644 /tmp/mir_panel.py /opt/klon/mir_panel.py; install -m 644 /tmp/kanaly_panel.py /opt/klon/kanaly_panel.py
  rm -rf /tmp/stat_seed; mkdir -p /tmp/stat_seed; cp /tmp/stat-seed-tg.csv /tmp/stat_seed/tg.csv; cp /tmp/stat-seed-yt.csv /tmp/stat_seed/yt.csv 2>/dev/null
  cat > /etc/systemd/system/stat-panel.service <<'U'
[Unit]
Description=Панель статистики Гуманетрии
[Service]
Type=oneshot
WorkingDirectory=/opt/razvedka
ExecStart=/opt/razvedka/venv/bin/python /opt/klon/stat_panel.py
ExecStart=/opt/razvedka/venv/bin/python /opt/klon/mir_panel.py
U
  cat > /etc/systemd/system/stat-panel.timer <<'U'
[Unit]
Description=Панель статистики, раз в сутки
[Timer]
OnCalendar=*-*-* 03:10:00 UTC
Persistent=true
[Install]
WantedBy=timers.target
U
  systemctl daemon-reload; systemctl enable --now stat-panel.timer 2>&1 | tail -1
  systemctl start stat-panel.service; result=$?
  journalctl -u stat-panel.service -n 25 --no-pager | cut -c1-400
  S=$(cat /var/lib/gonets/stat/sekret 2>/dev/null)
  [[ "$S" =~ ^[a-f0-9]{12}$ ]] || exit 1
  chmod a+rx "/opt/stack/vitrina/v/$S"
  chmod a+r "/opt/stack/vitrina/v/$S/"{stat,mir}.html
  for f in stat mir; do echo "$f HTTP $(curl -s -o /dev/null -w '%{http_code} %{size_download}' https://gumanetriya.ru/v/$S/$f.html)"; done
  exit "$result";;
refresh)
  # Update only collectors and their two pages. No unit writes or timer changes.
  set -e
  S=$(cat /var/lib/gonets/stat/sekret)
  [[ "$S" =~ ^[a-f0-9]{12}$ ]]
  pages="/opt/stack/vitrina/v/$S"
  before=$(systemctl show stat-panel.timer -p ActiveState -p UnitFileState -p TimersCalendar)
  [[ "$before" == *'ActiveState=active'* ]]
  if systemctl is-active --quiet stat-panel.service; then
    echo 'Сбор уже идёт; обновление не начато'; exit 1
  fi
  backup=$(mktemp -d /opt/backup/stat-panel-XXXXXX)
  cp -p /opt/klon/{stat_panel,panel_stil,mir_panel}.py "$pages/"{stat,mir}.html "$backup/"; cp -p /opt/klon/kanaly_panel.py "$backup/" 2>/dev/null || true; echo "копия: $backup"
  rollback() {
    echo 'Серверная проверка не прошла. Возвращаю предыдущий код и страницы.'
    cp -p "$backup/"{stat_panel,panel_stil,mir_panel}.py /opt/klon/
    cp -p "$backup/"{stat,mir}.html "$pages/"
    if [ -f "$backup/kanaly_panel.py" ]; then cp -p "$backup/kanaly_panel.py" /opt/klon/; else rm -f /opt/klon/kanaly_panel.py; fi
  }
  trap rollback ERR
  install -m 644 /tmp/{stat_panel,panel_stil,mir_panel,kanaly_panel}.py /opt/klon/
  since=$(date --iso-8601=seconds)
  systemctl start stat-panel.service
  journalctl -u stat-panel.service --since "$since" --no-pager | cut -c1-400
  grep -Fq 'Открытый канал RUTUBE' "$pages/stat.html"
  grep -Fq 'Видео в топе RUTUBE' "$pages/mir.html"
  grep -Fq 'Итого по каналам' "$pages/stat.html"
  grep -Fq 'Заказы — итог по n8n' "$pages/stat.html"
  head -c 3 "$pages/kanaly.csv" | od -An -tx1 | grep -q 'ef bb bf'
  echo "csv строк: $(wc -l < "$pages/kanaly.csv")"
  for f in stat mir kanaly; do
    [ "$f" = kanaly ] && ext=csv || ext=html
    response=$(curl -fsS --max-time 20 -o /dev/null -w '%{http_code} %{size_download}' "https://gumanetriya.ru/v/$S/$f.$ext")
    [[ "$response" == '200 '* ]]
    echo "$f.$ext HTTP $response"
  done
  after=$(systemctl show stat-panel.timer -p ActiveState -p UnitFileState -p TimersCalendar)
  [[ "$before" == "$after" ]]
  trap - ERR
  echo 'Расписание не менялось';;
itog) systemctl is-active stat-panel.timer; journalctl -u stat-panel.service -n 12 --no-pager | cut -c1-400;;
otkat) systemctl disable --now stat-panel.timer; echo выключен;;
esac
