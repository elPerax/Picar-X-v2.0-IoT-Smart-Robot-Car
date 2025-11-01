#!/usr/bin/env bash
set -euo pipefail

REMOTE="gdrive"                          # change if your remote has another name
LOG_DIR="/home/pi/picar-x/logs"
YDAY=${YDAY:-$(date -d "yesterday" +%F)}
DEST="${REMOTE}:RobotCar_M2/logs/${YDAY}/"
UPLOAD_LOG="${LOG_DIR}/upload_${YDAY}.log"

shopt -s nullglob
files=( "${LOG_DIR}/${YDAY}_".*.csv "${LOG_DIR}/${YDAY}_"*.csv "${LOG_DIR}/${YDAY}_*.csv" )
if (( ${#files[@]} == 0 )); then
  echo "No files for ${YDAY}" | tee -a "$UPLOAD_LOG"
  exit 0
fi

rclone mkdir "$DEST" || true
rclone copy "${files[@]}" "$DEST" \
  --transfers 4 --checkers 8 --bwlimit 2M \
  --log-file "$UPLOAD_LOG" --log-level INFO

echo "Uploaded ${#files[@]} file(s) for ${YDAY} to ${DEST}" | tee -a "$UPLOAD_LOG"
