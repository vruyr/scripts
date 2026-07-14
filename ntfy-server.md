# ntfy Server on the Mac mini

Self-hosted [ntfy](https://docs.ntfy.sh) push notification server, running as a Docker container under colima on the always-on Mac mini. It delivers download notifications from `yt-dlp-pasteboard` (sent by `yt-dlp-pasteboard-ntfy-send`) to the ntfy app on the iPhone.

The full flow:

1. iPhone Shortcut sends a video URL over SSH: `yt-dlp-pasteboard-tmux queue`.
2. `yt-dlp-pasteboard`, running in a detached tmux session, downloads it.
3. On each lifecycle event it runs `yt-dlp-pasteboard-ntfy-send`, which publishes to this server.
4. The server pokes the phone through ntfy.sh's APNs bridge (content stays local).
5. The ntfy app fetches the message from this server and shows the notification.


## Prerequisites

Everything runs on the Mac mini:

```sh
brew install colima docker
colima start
brew services start colima   # restart colima automatically after reboots
```


## Initial Setup


### Create the server config

```sh
mkdir -p ~/ntfy
```

Write `~/ntfy/server.yml`:

```yaml
# The URL the *iPhone* uses to reach this server. Use the Mac mini's
# LAN IP or an internal DNS name that also resolves over the VPN.
# Avoid Bonjour ".local" names - they do not resolve across a VPN.
base-url: "http://192.168.1.10:8080"

# Required for timely iOS delivery: Apple does not allow apps to keep
# background connections open, so the phone is woken through ntfy.sh's
# APNs bridge. Only a topic hash is forwarded upstream - the message
# content never leaves this server.
upstream-base-url: "https://ntfy.sh"

cache-file: /var/lib/ntfy/cache.db
auth-file: /var/lib/ntfy/auth.db
auth-default-access: deny-all
```


### Launch the container

```sh
docker run -d --name ntfy --restart unless-stopped -p 8080:80 -v ~/ntfy:/var/lib/ntfy -v ~/ntfy/server.yml:/etc/ntfy/server.yml:ro binwiederhier/ntfy serve
```


### Create the user, access rules, and token

With `auth-default-access: deny-all` nothing works until access is granted:

```sh
docker exec -it ntfy ntfy user add vruyr          # prompts for a password
docker exec -it ntfy ntfy access vruyr ytdl rw    # allow the ytdl topic
docker exec -it ntfy ntfy token add vruyr         # prints tk_... for scripts
```

The username and password are for the iOS app; the `tk_...` token is for `yt-dlp-pasteboard-ntfy-send` on the Mac.


## iOS App Setup

Install "ntfy" from the App Store, then:

1. Settings → Default server: the `base-url` value, e.g. `http://192.168.1.10:8080`.
2. Settings → Manage users: add the server with the username and password from above.
3. `+` → subscribe to topic `ytdl`.

Notes:

- The phone must be able to reach the server to fetch message content: at home that is the LAN, away from home connect the VPN. An on-demand VPN profile makes this seamless.
- The wake-up poke still arrives through ntfy.sh even while the server is unreachable; the notification appears once the app can fetch from the server again.


## Verify

From the Mac mini:

```sh
curl -H "Authorization: Bearer tk_yourtoken" -H "Title: Test" -d "Hello from the Mac mini" http://127.0.0.1:8080/ytdl
```

The notification should appear on the iPhone within a few seconds. Then test the script path end to end (see configuration below):

```sh
yt-dlp-pasteboard-ntfy-send "Hello via yt-dlp-pasteboard-ntfy-send"
echo "Hello via stdin" | yt-dlp-pasteboard-ntfy-send
```


## Day-to-Day Operations


### Health and logs

```sh
docker ps --filter name=ntfy
docker logs -f ntfy
```


### Restart / stop

```sh
docker restart ntfy
docker stop ntfy
```


### Upgrade

```sh
docker pull binwiederhier/ntfy
docker rm -f ntfy
# re-run the "Launch the container" command above
```


### Backup

All state (message cache, users, tokens) lives in `~/ntfy`. Copy that directory; `server.yml` is part of it.


### Tokens

```sh
docker exec -it ntfy ntfy token list vruyr
docker exec -it ntfy ntfy token remove vruyr tk_oldtoken
docker exec -it ntfy ntfy token add vruyr
```

After rotating, update `~/.config/yt-dlp-pasteboard-ntfy-send/config`.


## Wiring Into the Video Download Workflow


### Configure yt-dlp-pasteboard-ntfy-send

Write `~/.config/yt-dlp-pasteboard-ntfy-send/config` and make it private:

```sh
mkdir -p ~/.config/yt-dlp-pasteboard-ntfy-send
cat > ~/.config/yt-dlp-pasteboard-ntfy-send/config <<'EOF'
NTFY_SERVER="http://127.0.0.1:8080"
NTFY_TOPIC="ytdl"
NTFY_TOKEN="tk_yourtoken"
# Default events: started finished failed already-downloaded. Add
# retrying to also get a notification for every retry attempt:
# YT_DLP_PASTEBOARD_EVENTS="started retrying finished failed already-downloaded"
EOF
chmod 600 ~/.config/yt-dlp-pasteboard-ntfy-send/config
```

`yt-dlp-pasteboard-ntfy-send` runs on the Mac mini itself, so it can always use `127.0.0.1` regardless of VPN or network changes.


### Configure the downloader session

Write `~/.config/yt-dlp-pasteboard-tmux/config`:

```sh
mkdir -p ~/.config/yt-dlp-pasteboard-tmux
cat > ~/.config/yt-dlp-pasteboard-tmux/config <<'EOF'
YTDL_DIR="$HOME/Movies/Incoming"   # where .yt-dlp.config lives
YTDL_QUEUE="$HOME/.local/state/ytdl-queue.txt"
EOF
```

On the Mac, `yt-dlp-pasteboard-tmux` starts the downloader in a detached tmux session (if needed) and attaches to the TUI; press `q` to stop the downloader, or detach with `Ctrl-b d` to leave it running.


### iOS Shortcut

One shortcut, added to the share sheet:

1. Receive **Text** from Share Sheet — not **URLs**: with the URL input type the shortcut input does not arrive over SSH as stdin text, so nothing gets queued; **Text** works.
2. **Run Script Over SSH** — host: the Mac mini, script: `~/scripts/yt-dlp-pasteboard-tmux queue`, with *Input* set to **Shortcut Input** passed as **stdin**.
3. Optionally **Show Notification** ("queued").

The URL travels as stdin, never as part of a command line, so titles and URLs with special characters cannot break quoting or inject commands. The same command also starts the downloader session if it is not already running.

The SSH session is non-interactive and gets a minimal PATH; `yt-dlp-pasteboard-tmux` compensates by prepending `~/.local/bin`, `/opt/homebrew/bin`, and `/usr/local/bin` for itself and inside the downloader session, so standard installs of `tmux` and `uv` need no shell configuration. Only if they are installed somewhere unusual, add that directory to the PATH in `~/.zshenv` (which non-interactive zsh reads; `~/.zshrc` is not enough).

If a video does not get queued and no session appears, run the queue command manually — when the downloader dies right at startup, the command reports the error and prints the last lines of `~/.local/state/ytdl-session.log` (the downloader's stderr log):

```sh
ssh <mac-mini> '~/scripts/yt-dlp-pasteboard-tmux queue "https://example.com/test"'
```

To peek at the running TUI from the phone, use any SSH client (Termius, Blink) and run `~/scripts/yt-dlp-pasteboard-tmux`.
