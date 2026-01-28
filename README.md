# 🐺 wolf-eepy: Active Session Power Inhibitor & Healthchecker for Wolf

**wolf-eepy** is a companion service for the [Wolf](https://github.com/games-on-whales/wolf) cloud gaming system. Its job is to prevent host suspension/hibernations while Wolf game sessions ae active — ensuring smooth, uninterrupted play.

---

## ✨ Features

- **System Sleep Inhibition:** Uses systemd-inhibit to keep the host awake while streaming is active.
- **Healthcheck Endpoint:** Central lockfile `/tmp/wolf/healthstatus.lock` is used for unified health signaling.
- **Docker & Compose Ready:** Lightweight sidecar container, minimal config.
- **Secure by Design:** Only needs minimal host privileges if properly configured.

---

## 🚀 Quick Start (Docker Compose)

Sample `docker-compose.yml`:

```yaml
services:
  wolf:
    image: ghcr.io/games-on-whales/wolf:stable
    environment:
      - WOLF_SOCKET_PATH=/var/run/wolf/wolf.sock #set the socket location
      # ...other envs
    volumes:
      - socket:/var/run/wolf:rw # mount the volume for the socket
      # ...other volumes
    # ...other settings

  wolf-eepy:
    build: ./wolf-eepy
    container_name: wolf-eepy
    volumes:
      - socket:/var/run/wolf:ro # mount the volume for the socket as read only
      - /run/dbus/system_bus_socket:/run/dbus/system_bus_socket:rw # Needed for system sleep inhibition
    network_mode: host # Needed for some D-Bus/systemd actions
    # privileged: true  # Use only if sleep inhibition fails without it (see below)
    restart: unless-stopped

  volumes:
    socket: #define a volume for the socket
```

> **Note:**  
> The only host-interacting requirement is the `/run/dbus/system_bus_socket` mount, to let wolf-eepy talk to the host's systemd for inhibition. Use `privileged: true` only if absolutely necessary!

---

## 💡 How It Works

- **Session Detection:**  
   wolf-eepy monitors the Wolf API socket (`/var/run/wolf/wolf.sock`). When an active session/stream is detected, it launches `systemd-inhibit` with `sleep infinity` to block host sleep via D-Bus.
- **Sleep Release:**  
   When all streams end and a grace period passes, inhibition is released safely.
- **Container Health:**  
   Readiness and liveness is signaled through a lockfile (`/tmp/wolf/healthstatus.lock`).  
   - `healthy`/`warning`/`unhealthy` states are written atomically for fast, safe checks.
   - Healthcheck endpoint: runs `uv run wolf-healthcheck`.

---

## 🐳 Docker Usage

```bash
# Build the Docker image
docker build -t wolf-eepy .

# Run with host systemd dbus access
docker run --rm \
  --network host \
  -v /var/run/wolf:/var/run/wolf:ro \
  -v /run/dbus/system_bus_socket:/run/dbus/system_bus_socket \
  wolf-eepy
```

---

## 📝 License

This project is licensed under the MIT License.
(C) Games on Whales Community
