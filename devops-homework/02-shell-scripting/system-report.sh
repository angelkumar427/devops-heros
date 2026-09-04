#!/usr/bin/env bash
#
# system-report.sh
#
# Shell scripting homework: builds a small system report using variables,
# interactive input (read), the current date, hostname, username, disk
# usage, and process monitoring — writing results to a new directory/file
# via output redirection.
#
# Usage: ./system-report.sh

set -uo pipefail

# ---- Variables --------------------------------------------------------
current_date="$(date)"                 # 1. current date
current_hostname="$(hostname)"          # 2. hostname
current_user="$(whoami)"                 # 3. username
report_dir="$HOME/system_reports"         # directory we'll create
timestamp="$(date +%Y%m%d_%H%M%S)"
report_file="${report_dir}/report_${timestamp}.txt"
process_file="${report_dir}/processes_${timestamp}.txt"

# ---- Interactive input --------------------------------------------------
read -r -p "Enter a label/note for this report: " report_label
read -r -p "How many top processes (by CPU) should be listed? [default 5]: " proc_count
proc_count="${proc_count:-5}"

# ---- Create directory & report file (directory creation, file generation) --
mkdir -p "$report_dir"          # directory creation
touch "$report_file"            # file creation with touch
touch "$process_file"

{
  echo "===================================================="
  echo " SYSTEM REPORT"
  echo "===================================================="
  echo "Label       : ${report_label}"
  echo "Date        : ${current_date}"
  echo "Hostname    : ${current_hostname}"
  echo "User        : ${current_user}"
  echo
  echo "---- Disk usage (df -h) ----------------------------"
  df -h
  echo
  echo "---- Disk usage of home directory (du -sh) ---------"
  du -sh "$HOME" 2>/dev/null
  echo
  echo "---- Top ${proc_count} processes by CPU usage --------------"
  ps aux --sort=-%cpu | head -n "$((proc_count + 1))"
} > "$report_file"          # output redirection into the report file

# Separately capture full process list (process monitoring) to its own file
ps aux > "$process_file"    # output redirection into a second file

# ---- Summary to the terminal --------------------------------------------
echo
echo "Report generated for '${report_label}' by ${current_user}@${current_hostname}"
echo "  -> ${report_file}"
echo "  -> ${process_file}"
echo
echo "Preview:"
echo "----------------------------------------------------"
cat "$report_file"
