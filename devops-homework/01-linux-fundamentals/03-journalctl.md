# `journalctl` for System Logging

`journalctl` is the query tool for **systemd-journald**, the logging service built into systemd. Instead of scattered flat-file logs under `/var/log/`, systemd distros centralize structured, indexed logs (kernel, services, boot messages, auth, etc.) into a binary journal that `journalctl` reads.

Everything below was run on a real systemd host — an Ubuntu 24.04 machine (`systemd 255`) — so the output is live journal data, not a description. Full transcript: [`journalctl-demo.txt`](./journalctl-demo.txt).

```
$ journalctl --version | head -1
systemd 255 (255.4-1ubuntu8.15)

$ systemctl is-system-running
degraded
```

("degraded" just means at least one unit on the box has failed; the journal itself is fully functional.)

## Viewing system logs

```
$ journalctl --until "10 min ago" -n 8 --no-pager
Sep 04 ... colima kernel: vethf67fbb9 (unregistering): left promiscuous mode
Sep 04 ... colima kernel: docker0: port 1(vethf67fbb9) entered disabled state
Sep 04 ... colima systemd[1]: run-docker-netns-7d79eccb7001.mount: Deactivated successfully.
Sep 04 ... colima systemd-networkd[416]: docker0: Lost carrier
```

Each line carries a timestamp, the hostname, the process that emitted it (`kernel`, `systemd[1]`, `systemd-networkd[416]`) and the message — kernel, init and network events interleaved in one stream, which is exactly what journald centralises.

## Checking logs for a SPECIFIC service

This is the part that matters most day to day. First `systemctl status` for the summary:

```
$ systemctl status docker --no-pager | head -6
● docker.service - Docker Application Container Engine
     Loaded: loaded (/usr/lib/systemd/system/docker.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-09-03 23:26:57 IST; 20h ago
TriggeredBy: ● docker.socket
```

Then `journalctl -u <unit>` for that service's actual log lines:

```
$ journalctl -u docker.service -n 12 --no-pager
Sep 04 19:24:50 colima dockerd[1544]: ... msg="sbJoin: gwep4 ''->'17c4072f237f'" ep=netdemo net=bridge
Sep 04 19:28:26 colima dockerd[1544]: ... msg="sbJoin: gwep4 ''->'0bfc5b2b8a42'" ep=userdemo net=bridge
Sep 04 19:28:58 colima dockerd[1544]: ... msg="received task-delete event from containerd" ...

$ journalctl -u systemd-networkd.service -n 8 --no-pager
Sep 04 19:28:53 colima systemd-networkd[416]: vethf67fbb9: Link UP
Sep 04 19:28:53 colima systemd-networkd[416]: docker0: Gained carrier
Sep 04 19:28:58 colima systemd-networkd[416]: vethf67fbb9: Link DOWN
```

**What I understood from this:** `-u` narrows the whole system journal down to one unit, which turns "something is wrong with Docker" into a readable, ordered story. The Docker lines above are literally the containers created for the other homework tasks being attached to and removed from the bridge network, and the `systemd-networkd` lines are the *same events* seen from the network stack's point of view — the veth interface coming up and going down. Correlating one service's logs against another's, on one timeline, is the thing that makes journald more useful than separate log files.

`journalctl -u docker.service -f` follows a unit live (the transcript captures 3 seconds of this), which is the systemd equivalent of `tail -f`.

## Filtering by priority and by kernel-only

```
$ journalctl -p warning -b -u docker.service --no-pager | tail -8
$ journalctl -p err -b -u docker.service --no-pager | tail -4
(no output = this service logged nothing at err or worse this boot)

$ journalctl -k --until "10 min ago" -n 6 --no-pager
```

An empty result from `-p err` is a useful answer, not a failure: it means the service is genuinely clean this boot. Combining `-p` with `-u` is how you check one service for problems without wading through the whole system.

## Journal size and boots

```
$ journalctl --list-boots --no-pager | tail -2
$ journalctl --disk-usage
```

## Most useful commands

```bash
journalctl                       # all logs, oldest first, in the pager
journalctl -e                    # jump straight to the end (most recent)
journalctl -f                    # follow / tail -f equivalent, live stream
journalctl -n 50                 # last 50 lines
journalctl --no-pager            # print straight to stdout, no less/more

journalctl -u nginx.service      # logs for one specific systemd unit
journalctl -u nginx -f           # follow logs for just that unit

journalctl -k                    # kernel messages only (dmesg equivalent)
journalctl -b                    # logs since the current boot
journalctl -b -1                 # logs from the *previous* boot
journalctl --list-boots          # list all known boots with their IDs

journalctl --since "2026-09-01"           # time-bounded
journalctl --since "1 hour ago"
journalctl --since "09:00" --until "10:00"

journalctl -p err                # filter by priority: emerg/alert/crit/err/warning/notice/info/debug
journalctl -p err -b             # errors-and-worse, this boot only

journalctl _PID=1234             # filter by a structured field, e.g. a specific PID
journalctl _UID=1000             # logs from a specific user id

journalctl -o json-pretty        # structured JSON output, useful for piping into jq/log shippers
journalctl --disk-usage          # how much disk the journal itself is using
journalctl --vacuum-time=7d      # prune journal entries older than 7 days
journalctl --vacuum-size=500M    # prune down to a size cap
```

## Why it matters for DevOps

- One tool replaces grepping through `/var/log/syslog`, `/var/log/auth.log`, `/var/log/kern.log`, per-service log files, etc.
- `-u <service>` is the daily-driver command when a systemd-managed service (nginx, docker, sshd, a custom `.service` unit) is misbehaving — it's the first thing to run after `systemctl status <service>` shows a failure.
- `--since`/`--until` + `-p err` is the fast way to answer "what broke, and when" during an incident.
- Persistence: by default the journal may be volatile (RAM-only, cleared on reboot) unless `/var/log/journal/` exists and journald is configured for persistent storage (`Storage=persistent` in `/etc/systemd/journald.conf`) — worth checking on a fresh box if logs seem to vanish after reboot.

## Interview-style talking points

- `journalctl -u <service> -f` is the systemd equivalent of `tail -f /var/log/<service>.log`.
- Journal logs are binary and indexed (fast filtering by time/priority/unit/field) vs. plain-text logs which need `grep`.
- `journalctl -b -1` for "what happened right before the last crash/reboot" is one of the most useful incident-response commands on a systemd box.
