# Task 2 — Shell Scripting Assignment

`system-report.sh` is a single script that hits every requirement from the assignment:

| Requirement | Where it's done |
|---|---|
| Prints the current date | `current_date="$(date)"` → printed in the report |
| Hostname retrieval | `current_hostname="$(hostname)"` |
| Username display | `current_user="$(whoami)"` |
| Disk usage analysis | `df -h` and `du -sh "$HOME"` |
| Process monitoring | `ps aux --sort=-%cpu | head` for the top-N, plus a full `ps aux` dump |
| File creation with `touch` | `touch "$report_file"` and `touch "$process_file"` before the redirections |
| Variable usage | `current_date`, `current_hostname`, `current_user`, `report_dir`, `timestamp`, `report_file`, `process_file`, `report_label`, `proc_count` |
| Interactive input via `read` | Prompts for a report label and how many top processes to list |
| Directory creation | `mkdir -p "$report_dir"` (`~/system_reports/`) |
| File generation | Two timestamped files per run: `report_<ts>.txt` and `processes_<ts>.txt` |
| Output redirection | `{ ... } > "$report_file"` and `ps aux > "$process_file"` |

## Run it

```bash
chmod +x system-report.sh
./system-report.sh
# Enter a label/note for this report: <your text>
# How many top processes (by CPU) should be listed? [default 5]: <number>
```

Output lands in `~/system_reports/` as two timestamped files, and a preview is printed to the terminal.

## Sample run — all commands and their output

The assignment asks for the README to carry all the commands' output, so the
complete run is reproduced below rather than only linked.

Run non-interactively by feeding the two `read -p` prompts from a file, in a clean
`debian:stable-slim` container (`procps` installed for `ps`) so the transcripts show
a bare Linux system rather than a laptop full of unrelated desktop processes:

```bash
printf "Homework demo run\n8\n" > answers.txt
./system-report.sh < answers.txt
```

### Terminal output

```
Report generated for 'Homework demo run' by root@162f64ad194f
  -> /root/system_reports/report_20260903_184110.txt
  -> /root/system_reports/processes_20260903_184110.txt

Preview:
----------------------------------------------------
====================================================
 SYSTEM REPORT
====================================================
Label       : Homework demo run
Date        : Thu Sep  3 18:41:10 UTC 2026
Hostname    : 162f64ad194f
User        : root

---- Disk usage (df -h) ----------------------------
Filesystem             Size  Used Avail Use% Mounted on
overlay                 40G  3.7G   34G  10% /
tmpfs                   64M     0   64M   0% /dev
shm                     64M     0   64M   0% /dev/shm
lima-ec133fa2e4f94f92  927G  112G  815G  13% /hw
/dev/vdb1               40G  3.7G   34G  10% /etc/hosts
tmpfs                  2.9G     0  2.9G   0% /proc/acpi
tmpfs                  2.9G     0  2.9G   0% /proc/scsi
tmpfs                  2.9G     0  2.9G   0% /sys/firmware

---- Disk usage of home directory (du -sh) ---------
20K	/root

---- Top 8 processes by CPU usage --------------
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.0  0.0   2300  1248 ?        Ss   18:41   0:00 sleep 600
root          46  0.0  0.0      0     0 ?        Z    18:41   0:00 [dpkg-preconfigu] <defunct>
root         135  0.0  0.0   2404  1468 ?        Ss   18:41   0:00 sh -c ./system-report.sh < /tmp/answers.txt > /tmp/run-output.txt 2>&1
root         141  0.0  0.0   3900  3000 ?        S    18:41   0:00 bash ./system-report.sh
root         151  0.0  0.0   6004  3272 ?        R    18:41   0:00 ps aux --sort=-%cpu
root         152  0.0  0.0   2312  1196 ?        S    18:41   0:00 head -n 9
```

### The two files the script created

```
$ ls -la /root/system_reports/
-rw-r--r-- 1 root root  841 Sep  3 18:41 processes_20260903_184110.txt
-rw-r--r-- 1 root root 1824 Sep  3 18:41 report_20260903_184110.txt
```

**`report_<timestamp>.txt`** — written by the `{ ... } > "$report_file"` redirection. Its contents are the same report shown in the preview above (date, hostname, user, `df -h`, `du -sh`, top-N processes).

**`processes_<timestamp>.txt`** — written by the separate `ps aux > "$process_file"` redirection, holding the *full* process list rather than just the top N:

```
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.0  0.0   2300  1248 ?        Ss   18:41   0:00 sleep 600
root          46  0.0  0.0      0     0 ?        Z    18:41   0:00 [dpkg-preconfigu] <defunct>
root         135  0.0  0.0   2404  1468 ?        Ss   18:41   0:00 sh -c ./system-report.sh < /tmp/answers.txt > /tmp/run-output.txt 2>&1
root         141  0.0  0.0   3900  3000 ?        S    18:41   0:00 bash ./system-report.sh
root         153  0.0  0.0   6004  3260 ?        R    18:41   0:00 ps aux
```

### Reading the output

- **`Hostname : 162f64ad194f`** is the container ID — inside a container, `hostname` returns the short container ID unless `--hostname` is passed.
- **`overlay` as the root filesystem** in `df -h` is the container's overlay filesystem; `lima-ec133fa2e4f94f92` mounted at `/hw` is the bind-mounted project directory from the host.
- **`Z` / `<defunct>`** on PID 46 is a zombie: a finished process whose parent hasn't reaped it yet. It holds no memory (`VSZ`/`RSS` are 0) — only a slot in the process table.
- **`head -n 9` appears in its own output** because `ps aux --sort=-%cpu | head` runs both sides of the pipe concurrently, so `ps` sees `head` running.

### Raw files in this folder

- [`run-output.txt`](./run-output.txt) — the terminal transcript above, unedited
- [`sample-report-output.txt`](./sample-report-output.txt) — the generated report file
- [`sample-processes-output.txt`](./sample-processes-output.txt) — the generated process-list file
