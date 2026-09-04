#!/usr/bin/env bash
# Weekly Search Console check — runs headless via a systemd timer (or cron),
# writes a markdown report and fires a desktop notification when done.
set -euo pipefail

export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"

SITE_URL="${SITE_URL:?Set SITE_URL, e.g. https://www.example.com/ or sc-domain:example.com}"
base_dir="$HOME/.config/google-search-console"
report_dir="$HOME/search-console-reports"
mkdir -p "$report_dir"
report_file="$report_dir/$(date +%Y-%m-%d).md"
prev_report="$(find "$report_dir" -name '*.md' -newer /dev/null -printf '%T@ %p\n' 2>/dev/null | sort -rn | awk 'NR==2{print $2}')"

prompt=$(cat <<EOF
Weekly Google Search Console check for ${SITE_URL}. You are running headless
via a scheduled timer with no memory of earlier sessions — everything you
need is in this prompt.

Query script: $base_dir/venv/bin/python $base_dir/query.py
  Examples:
    <script> "${SITE_URL}" --days 7 --dimensions page --limit 25
    <script> "${SITE_URL}" --days 7 --dimensions query --limit 25

Task:
1. Run both queries (page, query) for the last 7 days.
2. If a previous report exists (${prev_report:-none}), read it and compare
   trends: new or disappeared top queries, position changes, CTR changes.
3. Flag anything notable: high impressions with 0 clicks despite a good
   position (<10), unusual CTR outliers, notable new queries, position
   drops on previously well-ranking pages.
4. Suggest concrete improvements where useful (e.g. title/meta description
   tweaks that better match what people actually search for). Do NOT make
   any automatic changes to website files — analysis and suggestions only.
5. Write a short markdown report to $report_file: a metrics overview,
   notable findings, 2-4 concrete improvement suggestions.
6. At the end, print ONLY a 2-3 sentence summary to stdout (used for the
   desktop notification) — everything else belongs in the report file.
EOF
)

summary="$(claude -p "$prompt" --allowedTools "Bash Write" --add-dir "$base_dir" --add-dir "$report_dir" 2>&1)"

gdbus call --session --dest org.freedesktop.Notifications \
    --object-path /org/freedesktop/Notifications \
    --method org.freedesktop.Notifications.Notify \
    "Search Console" 0 "search-console" "Weekly report is ready" \
    "${summary:0:200}" "[]" "{}" 20000 >/dev/null 2>&1 || true

echo "$summary"
