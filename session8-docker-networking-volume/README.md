# Session 8 — Docker Networking & Volumes

**Author:** Angel Kumar · 24bcs10011  
**Repository:** [angelkumar427/devops-heros](https://github.com/angelkumar427/devops-heros)

This folder contains session resources for Docker networking drivers, volume management, and multi-container architectures.

---

## Homework Submission & Evidence

The complete hands-on homework exercises corresponding to **Docker Networking & Volumes** are implemented, tested, and documented with real execution transcripts and screenshots in:

👉 **[`../devops-homework/06-docker-advanced/`](../devops-homework/06-docker-advanced/)**

### Summary of Tasks Completed:

| Task | Topic | Implementation & Evidence | Result |
|---|---|---|---|
| **Task 1** | **Docker Container Networking** | 3 containers (`frontend`, `backend`, `database`), 3 custom bridge networks (`frontend-net`, `backend-net`, `db-net`). Backend connected to 2 networks. DNS resolution & inter-tier connectivity verified. | ✅ [`container-networking/`](../devops-homework/06-docker-advanced/container-networking/) |
| **Task 2** | **Host Network Mode** | Apache2 (`httpd:2.4`) container deployed with `--network host` on port 80. Verified direct host binding with no port forwarding (`-p`). | ✅ [`host-network/`](../devops-homework/06-docker-advanced/host-network/) |
| **Task 3** | **Bind Mounts** | Nginx container with volume bind mount of `./site/index.html` displaying `"Hello students"`. File edited live on host to `"Hello students - edited live on the host"`, reflected instantly with 0 restarts. | ✅ [`bind-mounts/`](../devops-homework/06-docker-advanced/bind-mounts/) |
| **Task 4** | **Overlay Networks** | In-depth research on Docker overlay networks across multiple hosts, VXLAN tunnels, Swarm manager state synchronization, VIP load balancing, and hands-on multi-replica Swarm service demo. | ✅ [`overlay-network/`](../devops-homework/06-docker-advanced/overlay-network/) |

---

## Resources & Documentation
- [Docker Network Drivers](https://docs.docker.com/engine/network/drivers/)
- [Manage Data in Docker](https://docs.docker.com/engine/storage/)
- [Use Bind Mounts](https://docs.docker.com/engine/storage/bind-mounts/)
- [Overlay Networking Tutorial](https://docs.docker.com/engine/network/drivers/overlay/)
