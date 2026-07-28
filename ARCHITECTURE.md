# Architecture: domain → Railway

## Target

| Item | Where |
|------|--------|
| Domain `www.magicsandsdmc.com` | Keep at Hostinger (DNS only later) |
| Full website + booking + admin | Railway (this Django app) |
| Hostinger web hosting | Remove after cutover |

## Local URLs (port 8001)

- `/` marketing home
- `/about/` `/services/` `/destinations/` `/testimonials/` `/contact/`
- `/hotels/` hotel search (LiteAPI)
- `/partner-login/` `/partner-register/` → partner portal login/register (non-staff)
- `/partner/` → partner front-end (Nuitee hotel search + user dashboard)
- `/admin/login/` → website admin login (staff only)
- `/admin/` → hub (Marketing website **or** Booking system admin)
- `/admin/marketing/` → marketing CMS
- `/admin/booking/` → booking system admin dashboard
- `/admin/bookings/` `/admin/partners/`

## Cutover later

See **[DEPLOY.md](DEPLOY.md)** for Railway project creation, env vars, and Hostinger DNS.

1. Deploy to Railway (this repo)
2. Add custom domain `magicsandsdmc.com` / `www`
3. Update Hostinger DNS to Railway
4. Cancel Hostinger hosting when DNS is stable
