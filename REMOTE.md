# Open Magic Sands Booking from phone + laptop

## A) Same Wi‑Fi (easiest)

1. On the **laptop**, start the server bound to all interfaces:

```powershell
cd C:\Users\Win11\Projects\magic-sands-booking
.\.venv\Scripts\Activate.ps1
python manage.py runserver 0.0.0.0:8001
```

2. Find the laptop LAN IP (PowerShell):

```powershell
ipconfig
```

Look for `IPv4 Address` under Wi‑Fi (example: `192.168.1.42`).

3. On your **phone** (same Wi‑Fi), open:

`http://192.168.1.42:8001/`

If it fails, allow Python through Windows Firewall for private networks.

## B) Away from home (true remote)

Keep coding on the laptop; expose the site with a tunnel:

### Cloudflare Tunnel (free, no account needed for quick try)

```powershell
npx -y cloudflared tunnel --url http://127.0.0.1:8001
```

Use the `https://….trycloudflare.com` link on your phone.

### Or ngrok

```powershell
ngrok http 8001
```

## C) Project files on phone + laptop

This is **code**, not just the website preview:

1. Push the repo to GitHub (private).
2. On the laptop: clone/pull as usual in Cursor.
3. On phone: browse the repo in GitHub / GitHub mobile (view only), or use a cloud IDE later.

Cursor’s editor work stays on the **laptop**; the phone is best for **previewing the site** via A or B.

## Quick scripts

- `scripts\run-lan.ps1` — start server for phone on Wi‑Fi
- `scripts\show-lan-url.ps1` — print the phone URL
