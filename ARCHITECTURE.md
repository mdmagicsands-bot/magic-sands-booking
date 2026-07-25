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
- `/partner-login/` `/partner-register/`
- `/admin/login/` → website admin login
- `/admin/` → hub (Marketing website **or** Booking system)
- `/admin/marketing/` → marketing CMS
- `/admin/booking/` → booking dashboard
- `/admin/bookings/` `/admin/partners/`

## Cutover later

1. Deploy to Railway
2. Add custom domain `magicsandsdmc.com` / `www`
3. Update Hostinger DNS to Railway
4. Cancel Hostinger hosting when DNS is stable
