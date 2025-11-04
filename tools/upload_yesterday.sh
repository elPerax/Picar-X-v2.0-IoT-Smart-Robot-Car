#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="/home/pi/picar-x/logs"
REMOTE="gdrive:RobotCar_M2/logs"
# Use -u for UTC if your CSV timestamps are UTC. Remove -u if you want local time.
YDAY=${YDAY:-$(date -u -d "yesterday" +%F)}

UPLOAD_LOG="${LOG_DIR}/upload_${YDAY}.log"

# Make a dated folder in Drive (optional but neat)
rclone mkdir "${REMOTE}/${YDAY}" >/dev/null 2>&1 || true

# Upload ONLY yesterday's files from the logs directory
rclone copy "${LOG_DIR}" "${REMOTE}/${YDAY}" \
  --include "${YDAY}_*.csv" \
  --transfers=4 --checkers=8 --bwlimit=2M \
  --retries=5 --low-level-retries=10 \
  --log-file "${UPLOAD_LOG}" --log-level INFO

# (Optional) checksum manifest for evidence
if ls "${LOG_DIR}/${YDAY}_*.csv" >/dev/null 2>&1; then
  sha256sum "${LOG_DIR}/${YDAY}_".*.csv "${LOG_DIR}/${YDAY}_*.csv" 2>/dev/null \
    | tee "${LOG_DIR}/checksums_${YDAY}.txt" >/dev/null || true
  rclone copy "${LOG_DIR}/checksums_${YDAY}.txt" "${REMOTE}/${YDAY}" \
    --log-level INFO >> "${UPLOAD_LOG}" 2>&1 || true
fi

echo "Uploaded files for ${YDAY} to ${REMOTE}/${YDAY}" | tee -a "${UPLOAD_LOG}"