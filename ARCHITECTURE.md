# Architecture: domain → Railway



## Three separate deployments



| URL | App | Repo | Railway |

|-----|-----|------|---------|

| `www.magicsandsdmc.com` | Marketing site + CMS | **magic-sands-marketingsite** (this repo) | Marketing service |

| Booking domain (TBD) | Hotel booking + partner portal | Separate booking repo | Booking service |

| `portal.magicsandsdmc.com` | DMC enterprise admin | **voucher-system** | Admin service |



## Marketing Railway (`SITE_PROFILE=marketing`, default on Railway)



Public pages:



- `/` marketing home

- `/about/` `/services/` `/destinations/` `/testimonials/` `/contact/`

- `/partner-register/` partner registration (stays on marketing)

- `/admin/login/` → staff login → `/admin/marketing/` CMS



Redirected to `PUBLIC_BOOKING_URL` (separate booking service):



- `/hotels/` `/book/` `/partner/` `/partner-login/`



## Local full stack (port 8001, `SITE_PROFILE=full` default)



Everything above, plus:



- `/hotels/` hotel search (LiteAPI)

- `/partner-login/` → partner portal login

- `/partner/` → partner front-end (Nuitee hotel search + user dashboard)

- `/admin/booking/` booking system admin dashboard

- `/admin/bookings/` `/admin/partners/`



## Cutover



See **[DEPLOY.md](DEPLOY.md)** for Railway project creation, env vars, and Hostinger DNS.



1. Deploy marketing to Railway (this repo, marketing service only)

2. Add custom domain `magicsandsdmc.com` / `www` to the **marketing** Railway service

3. Update Hostinger DNS to Railway

4. Later: separate Git + Railway for booking; set `PUBLIC_BOOKING_URL` on marketing

