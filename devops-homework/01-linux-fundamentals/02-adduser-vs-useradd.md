# `adduser` vs `useradd`

## TL;DR

`useradd` is the low-level, POSIX-ish binary that creates a user account with whatever flags you pass it — and nothing more. `adduser` is a friendlier, interactive **Perl wrapper around `useradd`** (on Debian/Ubuntu) that asks questions, picks sane defaults, creates the home directory, copies skeleton files, and sets a password for you.

Confirmed on this box (Ubuntu 24.04):

```
$ file /usr/sbin/adduser /usr/sbin/useradd
/usr/sbin/adduser: Perl script text executable
/usr/sbin/useradd: ELF 64-bit LSB pie executable, x86-64 ...
```

`adduser` is literally a script; `useradd` is a compiled binary. This is the giveaway that one wraps the other, not the reverse.

## Key differences

| | `useradd` | `adduser` |
|---|---|---|
| Nature | Low-level compiled binary (part of `shadow-utils`) | High-level Perl script wrapper around `useradd`/`usermod`/`passwd` |
| Availability | All Linux distros (RHEL, CentOS, Ubuntu, Debian, ...) | Mainly Debian/Ubuntu family (also available, differently implemented, on RHEL-family via EPEL) |
| Interactivity | Non-interactive — you must pass every option as flags | Interactive by default — prompts for password, full name, room number, etc. |
| Home directory | NOT created unless you pass `-m` | Created automatically |
| Skeleton files (`/etc/skel`) | Only copied with `-m` | Copied automatically |
| Password | Not set — account is locked until you run `passwd` | Prompts you to set one interactively |
| Defaults | Whatever's in `/etc/default/useradd` and `/etc/login.defs`, easy to forget a flag | Sensible Debian defaults baked in, less room for mistakes |
| Typical use | Scripting/automation, where you want full explicit control | Humans creating accounts by hand |

## Commands

```bash
# useradd: explicit, nothing implied
useradd -m -s /bin/bash -c "Angel" -G sudo devuser
passwd devuser              # separate step — must set a password yourself

# adduser: interactive, does the above (and more) for you
adduser devuser
# → prompts for password, full name, room number, work phone, home phone,
#   other, then confirms; home dir + skeleton files created automatically
```

## Why Ubuntu docs/tutorials generally say "prefer `adduser`"

- Fewer footguns for a human at the terminal — you're less likely to forget `-m` and end up with a homeless user.
- Ubuntu's `adduser` also has sane `deluser`/`addgroup`/`delgroup` counterparts that mirror it.
- For scripting/automation (Ansible, Dockerfiles, provisioning scripts) `useradd` is usually preferred instead, precisely *because* it's non-interactive and 100% explicit — no risk of a script hanging on a prompt.

## Interview-style talking points

- `adduser` is Debian/Ubuntu-specific tooling; `useradd` is the portable, distro-agnostic primitive.
- If a Dockerfile or CI script hangs on user creation, it's almost always because `adduser` was used without `--disabled-password --gecos ""` (which suppresses its interactive prompts) instead of just using `useradd`.
- Both ultimately edit the same files: `/etc/passwd`, `/etc/shadow`, `/etc/group`.

## Hands-on: creating a test user with each command

Run on Debian 13 (trixie); full transcript in [`adduser-vs-useradd-demo.txt`](./adduser-vs-useradd-demo.txt).

**The recommended command on Debian/Ubuntu — `adduser`:**

```
$ adduser --disabled-password --gecos "" testuser

$ getent passwd testuser
testuser:x:1000:1000::/home/testuser:/bin/bash
$ getent group testuser
testuser:x:1000:
$ ls -la /home/testuser
-rw-r--r-- 1 testuser testuser  220 .bash_logout
-rw-r--r-- 1 testuser testuser 3526 .bashrc
-rw-r--r-- 1 testuser testuser  807 .profile
```

One command produced: the account, a **matching group**, a **home directory**, **skeleton dotfiles** copied from `/etc/skel`, and a real login shell (`/bin/bash`).

(`--disabled-password --gecos ""` only make it non-interactive for a scripted demo — run plain `adduser testuser` and it prompts for a password and the full-name fields instead. The `usermod: no changes` line in the transcript is Debian 13's `adduser` reporting that its final `usermod` pass had nothing left to adjust; the account is created correctly, as the checks after it show.)

**The same thing with bare `useradd`:**

```
$ useradd testuser2

$ getent passwd testuser2
testuser2:x:1001:1001::/home/testuser2:/bin/sh
$ ls -la /home/testuser2
ls: cannot access '/home/testuser2': No such file or directory
```

The account exists and `/etc/passwd` even *claims* a home directory — but it was never created, and the shell defaulted to `/bin/sh`. Logging in as this user would drop into a broken environment.

**`useradd` done properly needs the flags spelled out:**

```
$ useradd -m -s /bin/bash testuser3
$ getent passwd testuser3
testuser3:x:1002:1002::/home/testuser3:/bin/bash
$ ls -A /home/testuser3
.bash_logout  .bashrc  .profile
```

### Result side by side

| User | Created with | Home exists? | Shell |
|---|---|---|---|
| `testuser` | `adduser` | **yes** | `/bin/bash` |
| `testuser2` | `useradd` | **NO** | `/bin/sh` |
| `testuser3` | `useradd -m -s /bin/bash` | yes | `/bin/bash` |

`-m` and `-s` are the two flags people forget, and forgetting them is the single most common cause of "I made the user but they can't log in properly."

### Cleanup

```
$ deluser --remove-home testuser
$ userdel -r testuser2
$ userdel -r testuser3
$ getent passwd testuser testuser2 testuser3
(exit 2 — none of the three exist any more)
$ ls -A /home/
(empty)
```

`deluser --remove-home` / `userdel -r` are the mirror images: they remove the account **and** its home directory. Without `-r`, `userdel` leaves the home directory orphaned on disk.
