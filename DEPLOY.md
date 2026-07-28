# Deploy Magic Sands Booking to Railway

This Django app serves **www.magicsandsdmc.com** — marketing site, contact, partner
registration, hotel booking, and partner portal.

The enterprise voucher admin stays on a **separate** Railway service:
**portal.magicsandsdmc.com** (`voucher-system` repo).

---

## 1. Prerequisites

- GitHub repo with this project (push `main` or your deploy branch).
- [Railway](https://railway.app) account.
- Domain DNS at Hostinger (change DNS only after Railway is healthy).
- LiteAPI key (sandbox for testing, production key when going live).
- Hostinger SMTP mailbox for contact / partner emails (e.g. `noreply@magicsandsdmc.com`).

Ensure marketing assets are in the repo under `static/ms/` (images, CSS, uploads).
Without them, pages will load but images will 404.

---

## 2. Create the Railway project

1. Railway dashboard → **New project** → **Deploy from GitHub repo**.
2. Select the **magic-sands-booking** repository.
3. Railway detects `railway.toml` and uses `bash bin/start.sh` on deploy.

### Add PostgreSQL

1. In the same project: **+ New** → **Database** → **PostgreSQL**.
2. Open the web service → **Variables** → **Add reference** → link `DATABASE_URL`
   from the Postgres service.

---

## 3. Environment variables

In the **web service** → **Variables**, set:

| Variable | Example / notes |
|----------|-----------------|
| `DEBUG` | `False` |
| `SECRET_KEY` | Long random string (required in production) |
| `ALLOWED_HOSTS` | `www.magicsandsdmc.com,magicsandsdmc.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://www.magicsandsdmc.com,https://magicsandsdmc.com` |
| `MARKETING_SITE_URL` | `https://www.magicsandsdmc.com` |
| `PUBLIC_BOOKING_URL` | `https://www.magicsandsdmc.com` |
| `DATABASE_URL` | Reference from Postgres plugin |
| `LITEAPI_API_KEY` | Your LiteAPI / Nuitee key |
| `LITEAPI_PUBLIC_KEY` | `sandbox` or production public key |
| `EMAIL_HOST` | `smtp.hostinger.com` |
| `EMAIL_PORT` | `587` (TLS) or `465` (SSL) |
| `EMAIL_HOST_USER` | `noreply@magicsandsdmc.com` |
| `EMAIL_HOST_PASSWORD` | Mailbox password |
| `EMAIL_USE_TLS` | `True` (port 587) |
| `DEFAULT_FROM_EMAIL` | `noreply@magicsandsdmc.com` |
| `PARTNER_REGISTRATION_NOTIFY_EMAIL` | `oman@magicsandsdmc.com` |

Optional until you attach a custom domain:

```text
ALLOWED_HOSTS=www.magicsandsdmc.com,magicsandsdmc.com,your-service.up.railway.app
```

Railway also auto-adds `.up.railway.app` when `RAILWAY_*` env vars are present.

---

## 4. First deploy checklist

After the first successful deploy:

1. Open `https://<your-service>.up.railway.app/health/` → `{"status":"ok"}`.
2. Browse `/`, `/contact/`, `/partner-register/`.
3. Confirm static images load (`/static/ms/...`).
4. Create admin user (Railway shell or one-off command):

```bash
python manage.py seed_portal_users
```

**Change the default admin password immediately** (`admin@magicsandsdmc.com` / `admin123`).

Or create your own superuser:

```bash
python manage.py createsuperuser
```

5. Log in at `/admin/login/`.

---

## 5. Custom domain (Hostinger DNS)

When the Railway URL looks good:

1. Web service → **Settings** → **Networking** → **+ Custom Domain**.
2. Add `www.magicsandsdmc.com` and `magicsandsdmc.com`.
3. Copy the DNS records Railway shows (CNAME + TXT verify).

In **Hostinger DNS** for `magicsandsdmc.com`:

| Type | Name | Value |
|------|------|--------|
| CNAME | `www` | Railway target (`*.up.railway.app`) |
| As Railway instructs | `@` or ALIAS | Apex domain |
| TXT | per Railway | Domain verification |

**Do not** point `www` at `portal.magicsandsdmc.com` — that is the enterprise admin.

Lower DNS TTL to **300** one day before cutover. Wait for SSL “ready” in Railway.

Update variables if needed:

```text
MARKETING_SITE_URL=https://www.magicsandsdmc.com
PUBLIC_BOOKING_URL=https://www.magicsandsdmc.com
```

---

## 6. Retire Hostinger web hosting

After `https://www.magicsandsdmc.com` serves the Railway app for 24–48 hours:

- Cancel or pause Hostinger **web hosting** (keep domain + email mailboxes).
- Remove old PHP/Laravel files from `public_html` if you no longer need rollback.

---

## 7. Partner registration uploads

Uploaded documents are stored in `media/` on the container disk. Railway disks
are **ephemeral** unless you attach a **Volume** mounted at `/app/media` (or your
`MEDIA_ROOT`). For production partner registrations, plan either:

- Railway volume for `media/`, or
- Object storage (S3/R2) in a later iteration.

---

## 8. Local production smoke test

```powershell
cd C:\Users\Win11\Projects\magic-sands-booking
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DEBUG="False"
$env:SECRET_KEY="local-prod-smoke-test-key"
$env:ALLOWED_HOSTS="127.0.0.1,localhost"
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi:application --bind 127.0.0.1:8001
```

---

## 9. Troubleshooting

| Symptom | Fix |
|---------|-----|
| 404 on Railway URL | Check deploy logs; confirm `ALLOWED_HOSTS` includes `.up.railway.app` |
| No CSS / images | Run `collectstatic`; confirm `static/ms/` is in git |
| 500 on contact submit | Set SMTP variables; check Railway logs |
| CSRF error on forms | Add site origin to `CSRF_TRUSTED_ORIGINS` |
| Health check failing | Open `/health/` manually; increase `healthcheckTimeout` in `railway.toml` |

---

## Architecture reminder

| URL | App | Repo |
|-----|-----|------|
| `www.magicsandsdmc.com` | Marketing + booking + partners | **magic-sands-booking** (this repo) |
| `portal.magicsandsdmc.com` | DMC enterprise admin / vouchers | **voucher-system** |
