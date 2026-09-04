# DevOps Homework — Submission

Completed solutions for the DevOps homework: Linux fundamentals, shell scripting, networking, Git/GitHub, Docker fundamentals, and advanced Docker (multi-stage builds + networking/volumes).

Everything here was **actually run** — every task folder contains the working code/config plus a `*-output.txt` transcript of real captured command output, and the Docker tasks include real browser screenshots of the running containers.

The course materials these tasks accompany are in the `session*/` folders at the root of this repository.

## Contents

| # | Task | Folder | Related session material |
|---|---|---|---|
| 1 | Linux Fundamentals — soft/hard links, `adduser` vs `useradd`, `journalctl`, command reference | [`01-linux-fundamentals/`](./01-linux-fundamentals/) | [`session2-linux/`](../session2-linux/) |
| 2 | Shell Scripting — `system-report.sh` | [`02-shell-scripting/`](./02-shell-scripting/) | [`session3-shell-scripting/`](../session3-shell-scripting/) |
| 3 | Networking Fundamentals — commands run + explained | [`03-networking/`](./03-networking/) | [`session4-networking/`](../session4-networking/) |
| 4 | Git/GitHub — commit syntax, branching + cherry-pick | [`04-git-github/`](./04-git-github/) | [`session5-git-github/`](../session5-git-github/) |
| 5 | Docker Fundamentals — 6 Hello World containers | [`05-docker-fundamentals/`](./05-docker-fundamentals/) | [`session6-7-docker/`](../session6-7-docker/) |
| 6 | Advanced Docker — multi-stage builds + networking, host mode, bind mounts, overlay | [`06-docker-advanced/`](./06-docker-advanced/) | [`session8-docker-networking-volume/`](../session8-docker-networking-volume/) |

Each task folder has its own `README.md` explaining what was done and linking to the raw output backing it up.

## Evidence at a glance

| Requirement | Where |
|---|---|
| Six Hello World apps, correct folder structure, all verified | [`05-docker-fundamentals/`](./05-docker-fundamentals/) — 6 screenshots |
| Multi-stage build serving the required string on port 8080 | [`06-docker-advanced/multi-stage-build/`](./06-docker-advanced/multi-stage-build/) |
| Name + enrollment number submission doc | [`06-docker-advanced/multi-stage-build/SUBMISSION.md`](./06-docker-advanced/multi-stage-build/SUBMISSION.md) |
| 3 containers / 3 networks / backend on 2 networks | [`06-docker-advanced/container-networking/`](./06-docker-advanced/container-networking/) |
| Apache2 on the host network, port 80 | [`06-docker-advanced/host-network/`](./06-docker-advanced/host-network/) |
| Bind mount serving "Hello students", edited live | [`06-docker-advanced/bind-mounts/`](./06-docker-advanced/bind-mounts/) |
| Overlay network research + hands-on Swarm demo | [`06-docker-advanced/overlay-network/`](./06-docker-advanced/overlay-network/) |

## Environment the Docker tasks were run in

Docker **29.5.2** on an `aarch64` (Apple Silicon) Docker host, with Colima providing the Linux VM that Docker requires on macOS. Three platform quirks are documented where they show up rather than papered over:

- Python's Hello World is published on host port **5001**, because macOS itself occupies port 5000 (Control Center / AirPlay Receiver).
- `--network host` shares the **VM's** network namespace, not macOS's.
- Swarm's routing mesh does not work under Colima, so the overlay network is verified by container-to-container traffic over the overlay instead.

## A note on the Git demos

Task 4 needed real git repositories to demonstrate commit behaviour and cherry-picking. A git repo cannot be nested inside another and stay browsable on GitHub, so each demo's full history ships as a **git bundle** (`history.bundle`) beside its working files — restore either with `git clone history.bundle <dir>`. See [`04-git-github/README.md`](./04-git-github/README.md).
