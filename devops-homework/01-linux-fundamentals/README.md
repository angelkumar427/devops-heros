# Task 1 — Linux Fundamentals

Four sub-tasks: soft vs hard links, `adduser` vs `useradd`, `journalctl`, and a command reference. Each was actually run; the key results are summarised here and the full write-ups and raw transcripts are linked from each section.

## 1. Soft links vs hard links

[Write-up](./01-soft-vs-hard-links.md) · [raw transcript](./linkdemo-output.txt)

```
$ ln original.txt hardlink.txt          # hard link
$ ln -s original.txt softlink.txt       # soft (symbolic) link

$ ls -li
1171855 -rw-r--r-- 2 root root 35 hardlink.txt
1171855 -rw-r--r-- 2 root root 35 original.txt      <- same inode, link count 2
1171857 lrwxrwxrwx 1 root root 12 softlink.txt -> original.txt
```

Then the decisive test — **delete the original**:

```
$ rm original.txt

$ cat hardlink.txt      # still works
This is the original file content.

$ cat softlink.txt      # broken
cat: softlink.txt: No such file or directory
```

| | Hard link | Soft link |
|---|---|---|
| What it stores | Another name for the **same inode** | A **path string** to the target |
| Survives deleting the original | **Yes** — data lives until the last link goes | **No** — becomes a dangling link |
| Can cross filesystems | No | Yes |
| Can point at a directory | No (except `.`/`..`) | Yes |
| `ls -li` shows | Same inode number, link count > 1 | Own inode, `l` file type, `-> target` |

**The core idea:** a hard link is a second *name* for the data, so the data has no single "original". A soft link is just a signpost — delete what it points at and the signpost still exists but points nowhere.

## 2. `adduser` vs `useradd`

[Write-up](./02-adduser-vs-useradd.md) · [raw transcript](./adduser-vs-useradd-demo.txt)

`adduser` is a **Perl script wrapping** `useradd` (the compiled binary) on Debian/Ubuntu, and it's the recommended one. A test user was created with each to show the difference:

| User | Created with | Home dir created? | Shell |
|---|---|---|---|
| `testuser` | `adduser` | **yes**, with `/etc/skel` dotfiles + matching group | `/bin/bash` |
| `testuser2` | `useradd` | **NO** — `/etc/passwd` claims one that doesn't exist | `/bin/sh` |
| `testuser3` | `useradd -m -s /bin/bash` | yes | `/bin/bash` |

**The core idea:** `useradd` does exactly what you tell it and nothing more. Forgetting `-m` (create home) and `-s` (set shell) is the usual reason a freshly created user "can't log in properly". `adduser` handles both, plus the group and password prompt, by default. All three users were deleted afterwards with `deluser --remove-home` / `userdel -r`, verified.

## 3. `journalctl`

[Write-up](./03-journalctl.md) · [raw transcript](./journalctl-demo.txt)

Run against a live systemd host (Ubuntu 24.04, `systemd 255`), covering system logs, per-service logs, live follow, priority filters, kernel-only, boots and disk usage. The command that matters most day to day:

```
$ journalctl -u docker.service -n 12 --no-pager
Sep 04 19:24:50 colima dockerd[1544]: ... msg="sbJoin: gwep4 ''->'17c4072f237f'" ep=netdemo net=bridge
Sep 04 19:28:58 colima dockerd[1544]: ... msg="received task-delete event from containerd" ...

$ journalctl -u systemd-networkd.service -n 8 --no-pager
Sep 04 19:28:53 colima systemd-networkd[416]: vethf67fbb9: Link UP
Sep 04 19:28:58 colima systemd-networkd[416]: vethf67fbb9: Link DOWN
```

**The core idea:** journald centralises kernel, init and every service's logs into one indexed, structured store, so `-u <unit>` turns "something's wrong with Docker" into a readable timeline — and lets you line one service's logs up against another's. The two excerpts above are the same events from two angles: containers from the other homework tasks attaching to the bridge, and the veth interface coming up and down as they do.

## 4. Linux command reference

[`04-linux-command-reference.md`](./04-linux-command-reference.md) — a quick-reference guide to the essential commands (navigation, files, permissions, processes, search, archives, disk, networking, packages), grouped by what you're trying to do, with the purpose and basic usage of each.
