# Hostinger package (marketing site only)

Upload these files to Hostinger. They only host **Partner Login** and **Partner Registration**.  
All booking/admin systems run on **Railway**.

## Architecture

```text
magicsandsdmc.com (Hostinger)
  /partner-login/      → static page → POST → Railway /gateway/partner-login/
  /partner-register/   → static page → POST → Railway /gateway/partner-register/

Railway booking app
  /admin/              → partner admin dashboard
  /admin/bookings/     → bookings
  /admin/partners/     → registration requests
  /                    → guest hotel search & book
  /gateway/...         → receives Hostinger form posts
```

## Files to upload

### `public_html/partner-login/`
- `index.html`  (rename from this package’s index.html — already named)
- `partner-login.css`
- `config.js`

### `public_html/partner-register/`
- Copy `register.html` → upload as `index.html`
- Same `partner-login.css`
- Same `config.js`

Or upload the whole folder and adjust paths.

## Configure Railway URL

Edit `config.js` on Hostinger after Railway deploy:

```js
BOOKING_APP_URL: "https://YOUR-APP.up.railway.app",
```

Local test:

```js
BOOKING_APP_URL: "http://127.0.0.1:8001",
```

Note: browsers block posts from `https://magicsandsdmc.com` to `http://127.0.0.1` (mixed content).  
Test Hostinger → Railway only when Railway has an **https** URL.

## hPanel steps

1. hPanel → File Manager → `public_html`
2. Create `partner-login` and `partner-register`
3. Upload files as above
4. Set `BOOKING_APP_URL` in both folders’ `config.js`
