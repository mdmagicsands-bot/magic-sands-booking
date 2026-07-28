# Magic Sands Booking

Guest-facing hotel booking site under the **Magic Sands** brand. Guests search and book **any hotel** through [LiteAPI / Nuitee Connect](https://liteapi.travel/).

Flow: **Places / vibe search → rates → hotel detail → guest details → LiteAPI payment → confirmation**.

## Stack

- Python 3.12 + Django 6
- SQLite (local)
- LiteAPI sandbox for live hotel inventory

## Local marketing site

```powershell
cd C:\Users\Win11\Projects\magic-sands-booking
.\.venv\Scripts\Activate.ps1
python manage.py runserver 127.0.0.1:8001
```

Phone on same Wi‑Fi: see [REMOTE.md](REMOTE.md) or run `.\scripts\run-lan.ps1`

- Website: http://127.0.0.1:8001/
- Hotel booking: http://127.0.0.1:8001/hotels/
- Partner login: http://127.0.0.1:8001/partner-login/
- Admin: http://127.0.0.1:8001/admin/login/

Later: deploy this Django app to Railway, then point `www.magicsandsdmc.com` DNS to Railway and retire Hostinger hosting.

## Setup

1. Create a free sandbox API key at [liteapi.travel](https://liteapi.travel/) (keys start with `sand_` / `sandbox_`).

2. From this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

3. Edit `.env` and set `LITEAPI_API_KEY` (and keep `LITEAPI_PUBLIC_KEY=sandbox`).

4. Migrate and run (always use port **8001** locally — voucher-system uses **8000**):

```powershell
python manage.py migrate
python manage.py createsuperuser
.\bin\dev.ps1
```

5. Open http://127.0.0.1:8001/ — search a city (pick a suggestion) or use vibe search.

Partner admin: http://127.0.0.1:8001/admin/login/

DMC enterprise admin (separate repo): http://127.0.0.1:8000/admin/

## Logins (separate)

| Role | URL | Demo credentials | Lands on |
|------|-----|------------------|----------|
| **Website admin** | http://127.0.0.1:8001/admin/login/ | `admin@magicsandsdmc.com` / `admin123` | Admin hub → marketing or booking admin |
| **Partner portal** | http://127.0.0.1:8001/partner-login/ | `demo@magicsandsdmc.com` / `Demo123` | Nuitee hotel search + partner dashboard (`/partner/`) |

Seed both demo users:

```powershell
python manage.py seed_portal_users
```

- Admin hub: http://127.0.0.1:8001/admin/
- Booking admin: http://127.0.0.1:8001/admin/booking/
- Partner dashboard: http://127.0.0.1:8001/partner/
- Django system admin (models): http://127.0.0.1:8001/django-admin/

## Payments (sandbox)

On the payment page use Stripe test card:

- Card: `4242 4242 4242 4242`
- Any future expiry, any CVC

## Project layout

- `hotels/` — LiteAPI client, search, results, hotel detail
- `bookings/` — checkout, payment return, confirmation, `Booking` model
- `templates/` — guest UI
- `static/css/site.css` — Magic Sands styling

## Notes

- All LiteAPI calls are **server-side** (API key never exposed to the browser).
- Payment uses the LiteAPI Payment SDK; booking is finalized on `/book/payment/return/`.
- Production: swap to a `prod_` key and set `LITEAPI_PUBLIC_KEY=live`.
