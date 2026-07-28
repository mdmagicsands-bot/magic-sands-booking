# Deploy Magic Sands marketing site to Railway



This Railway service serves **www.magicsandsdmc.com** — the public marketing website,

contact form, partner registration, and marketing CMS only.



Hotel booking, partner login, and the partner portal run on a **separate Git repo and

Railway service** (see `BOOKING_SITE_URL` / `PUBLIC_BOOKING_URL`).



The enterprise voucher admin stays on another Railway service:

**portal.magicsandsdmc.com** (`voucher-system` / `magic-sands-enterprise-platform` repo).



---



## Three separate deployments



| URL | App | Repo | Railway |

|-----|-----|------|---------|

| `www.magicsandsdmc.com` | Marketing site + CMS | **magic-sands-marketingsite** (this repo) | Marketing service |

| Booking domain (e.g. `book.magicsandsdmc.com`) | Hotel booking + partner portal | Separate booking repo (TBD) | Booking service |

| `portal.magicsandsdmc.com` | DMC enterprise admin / vouchers | **voucher-system** | Admin service |



On Railway, this repo defaults to **`SITE_PROFILE=marketing`** (booking routes redirect to

`PUBLIC_BOOKING_URL`). Local dev on port **8001** runs the full stack unless you set

`SITE_PROFILE=marketing`.



---



## 1. Prerequisites



- GitHub repo: **magic-sands-marketingsite** (push `main`).

- [Railway](https://railway.app) account — one project for marketing only.

- Domain DNS at Hostinger (change DNS only after Railway is healthy).

- Hostinger SMTP mailbox for contact / partner emails (e.g. `noreply@magicsandsdmc.com`).



Ensure marketing assets are in the repo under `static/ms/` (images, CSS, uploads).

Without them, pages will load but images will 404.



**Do not** point this Railway project at the booking repo, or vice versa.



---



## 2. Create the Railway project (marketing only)



1. Railway dashboard → **New project** → **Deploy from GitHub repo**.

2. Select the **magic-sands-marketingsite** repository.

3. Railway detects `railway.toml` and uses `bash bin/start.sh` on deploy.

4. Leave **`SITE_PROFILE` unset** on Railway — it auto-defaults to `marketing`.



### Add PostgreSQL



1. In the same project: **+ New** → **Database** → **PostgreSQL**.

2. Open the web service → **Variables** → **Add reference** → link `DATABASE_URL`

   from the Postgres service.



---



## 3. Environment variables (marketing service)



In the **web service** → **Variables**, set:



| Variable | Example / notes |

|----------|-----------------|

| `DEBUG` | `False` |

| `SECRET_KEY` | Long random string (required in production) |

| `ALLOWED_HOSTS` | `www.magicsandsdmc.com,magicsandsdmc.com` |

| `CSRF_TRUSTED_ORIGINS` | `https://www.magicsandsdmc.com,https://magicsandsdmc.com` |

| `MARKETING_SITE_URL` | `https://www.magicsandsdmc.com` |

| `PUBLIC_BOOKING_URL` | Future booking site, e.g. `https://book.magicsandsdmc.com` |

| `BOOKING_SITE_URL` | Same as `PUBLIC_BOOKING_URL` (optional alias) |

| `DATABASE_URL` | Reference from Postgres plugin |

| `EMAIL_HOST` | `smtp.hostinger.com` |

| `EMAIL_PORT` | `587` (TLS) or `465` (SSL) |

| `EMAIL_HOST_USER` | `noreply@magicsandsdmc.com` |

| `EMAIL_HOST_PASSWORD` | Mailbox password |

| `EMAIL_USE_TLS` | `True` (port 587) |

| `DEFAULT_FROM_EMAIL` | `noreply@magicsandsdmc.com` |

| `PARTNER_REGISTRATION_NOTIFY_EMAIL` | `oman@magicsandsdmc.com` |



**Not required on the marketing Railway service:** `LITEAPI_API_KEY` (booking only).



Optional until you attach a custom domain:



```text

ALLOWED_HOSTS=www.magicsandsdmc.com,magicsandsdmc.com,your-service.up.railway.app

```



Railway also auto-adds `.up.railway.app` when `RAILWAY_*` env vars are present.



---



## 4. First deploy checklist



After the first successful deploy:



1. Open `https://<your-service>.up.railway.app/health/` →

   `{"status":"ok","service":"magic-sands-marketing","profile":"marketing"}`.

2. Browse `/`, `/contact/`, `/partner-register/`.

3. Confirm `/hotels/` and `/partner-login/` redirect to `PUBLIC_BOOKING_URL`.

4. Confirm static images load (`/static/ms/...`).

5. Create a staff user for the marketing CMS:



```bash

python manage.py createsuperuser

```



6. Log in at `/admin/login/` → redirects to `/admin/marketing/`.



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



---



## 6. Booking service (separate — later)



When the booking app has its own repo and Railway project:



1. Create a new GitHub repo and Railway service for booking only.

2. Set `SITE_PROFILE=full` (or omit — non-Railway defaults to full locally).

3. Set `ALLOWED_HOSTS` and `PUBLIC_BOOKING_URL` on the booking service.

4. On this marketing service, set `PUBLIC_BOOKING_URL` to the live booking domain.

5. Point booking DNS (e.g. `book.magicsandsdmc.com`) at the booking Railway service.



Until then, marketing redirects for `/hotels/`, `/book/`, `/partner/`, and `/partner-login/`

go to whatever URL you set in `PUBLIC_BOOKING_URL`.



---



## 7. Retire Hostinger web hosting



After `https://www.magicsandsdmc.com` serves the Railway marketing app for 24–48 hours:



- Cancel or pause Hostinger **web hosting** (keep domain + email mailboxes).

- Remove old PHP/Laravel files from `public_html` if you no longer need rollback.



---



## 8. Local development



Full stack (marketing + booking) on port **8001**:



```powershell

cd C:\Users\Win11\Projects\magic-sands-booking

.\bin\dev.ps1

```



Marketing-only smoke test locally:



```powershell

$env:SITE_PROFILE="marketing"

$env:PUBLIC_BOOKING_URL="http://127.0.0.1:8001"

python manage.py runserver 127.0.0.1:8001

```



---



## 9. Troubleshooting



| Symptom | Fix |

|---------|-----|

| Health shows `"profile":"full"` on Railway | Set `SITE_PROFILE=marketing` or redeploy with Railway env vars present |

| 404 on Railway URL | Check deploy logs; confirm `ALLOWED_HOSTS` includes `.up.railway.app` |

| No CSS / images | Run `collectstatic`; confirm `static/ms/` is in git |

| 500 on contact submit | Set SMTP variables; check Railway logs |

| CSRF error on forms | Add site origin to `CSRF_TRUSTED_ORIGINS` |

| `/hotels/` shows marketing 404 | Expected if `PUBLIC_BOOKING_URL` is wrong — set booking domain |

| Health check failing | Open `/health/` manually; increase `healthcheckTimeout` in `railway.toml` |

