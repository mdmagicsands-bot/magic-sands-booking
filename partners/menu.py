"""Booking admin sidebar menu — B2B hotel reservation system (Nuitee + direct)."""

from __future__ import annotations

MENU_GROUPS = [
    {
        "label": "Overview",
        "items": [
            {
                "label": "Dashboard",
                "url_name": "booking_admin_dashboard",
                "match": ["booking_admin_dashboard"],
            },
            {
                "label": "Live hotel search",
                "url_name": "admin_live_search",
                "match": ["admin_live_search"],
            },
        ],
    },
    {
        "label": "Reservations",
        "items": [
            {
                "label": "All bookings",
                "url_name": "partner_bookings",
                "match": ["partner_bookings", "partner_booking_detail"],
            },
            {
                "label": "Pending payment",
                "url_name": "partner_bookings_pending",
                "match": ["partner_bookings_pending"],
            },
            {
                "label": "Confirmed",
                "url_name": "partner_bookings_confirmed",
                "match": ["partner_bookings_confirmed"],
            },
            {
                "label": "Cancellations",
                "url_name": "partner_bookings_cancelled",
                "match": ["partner_bookings_cancelled"],
            },
            {
                "label": "Failed / errors",
                "url_name": "partner_bookings_failed",
                "match": ["partner_bookings_failed"],
            },
        ],
    },
    {
        "label": "Inventory",
        "items": [
            {
                "label": "Nuitee / LiteAPI hotels",
                "url_name": "admin_mod_nuitee_hotels",
                "match": ["admin_mod_nuitee_hotels"],
            },
            {
                "label": "Direct contract hotels",
                "url_name": "admin_mod_direct_hotels",
                "match": ["admin_mod_direct_hotels"],
            },
            {
                "label": "Room types & allotments",
                "url_name": "admin_mod_allotments",
                "match": ["admin_mod_allotments"],
            },
            {
                "label": "Stop-sale / close-outs",
                "url_name": "admin_mod_stopsale",
                "match": ["admin_mod_stopsale"],
            },
        ],
    },
    {
        "label": "Rates & contracts",
        "items": [
            {
                "label": "Direct contracts",
                "url_name": "admin_mod_contracts",
                "match": ["admin_mod_contracts"],
            },
            {
                "label": "Contracted rates",
                "url_name": "admin_mod_contract_rates",
                "match": ["admin_mod_contract_rates"],
            },
            {
                "label": "Markups & commissions",
                "url_name": "admin_mod_markups",
                "match": ["admin_mod_markups"],
            },
            {
                "label": "Promotions & specials",
                "url_name": "admin_mod_promotions",
                "match": ["admin_mod_promotions"],
            },
        ],
    },
    {
        "label": "B2B partners",
        "items": [
            {
                "label": "New registrations",
                "url_name": "partner_requests",
                "query": "?status=pending",
                "match": ["partner_requests", "partner_request_detail"],
            },
            {
                "label": "Partner agencies",
                "url_name": "admin_mod_agencies",
                "match": ["admin_mod_agencies"],
            },
            {
                "label": "Credit & limits",
                "url_name": "admin_mod_partner_credit",
                "match": ["admin_mod_partner_credit"],
            },
            {
                "label": "B2B rate plans",
                "url_name": "admin_mod_b2b_rates",
                "match": ["admin_mod_b2b_rates"],
            },
        ],
    },
    {
        "label": "Guests & CRM",
        "items": [
            {
                "label": "Guest profiles",
                "url_name": "admin_mod_guests",
                "match": ["admin_mod_guests"],
            },
            {
                "label": "Guest communications",
                "url_name": "admin_mod_guest_comms",
                "match": ["admin_mod_guest_comms"],
            },
        ],
    },
    {
        "label": "Finance",
        "items": [
            {
                "label": "Invoices",
                "url_name": "admin_mod_invoices",
                "match": ["admin_mod_invoices"],
            },
            {
                "label": "Payments",
                "url_name": "admin_mod_payments",
                "match": ["admin_mod_payments"],
            },
            {
                "label": "Refunds",
                "url_name": "admin_mod_refunds",
                "match": ["admin_mod_refunds"],
            },
            {
                "label": "Supplier payables",
                "url_name": "admin_mod_payables",
                "match": ["admin_mod_payables"],
            },
        ],
    },
    {
        "label": "Operations",
        "items": [
            {
                "label": "Vouchers",
                "url_name": "admin_mod_vouchers",
                "match": ["admin_mod_vouchers"],
            },
            {
                "label": "Transfers",
                "url_name": "admin_mod_transfers",
                "match": ["admin_mod_transfers"],
            },
            {
                "label": "Excursions / extras",
                "url_name": "admin_mod_extras",
                "match": ["admin_mod_extras"],
            },
            {
                "label": "Support tickets",
                "url_name": "admin_mod_tickets",
                "match": ["admin_mod_tickets"],
            },
        ],
    },
    {
        "label": "Reports",
        "items": [
            {
                "label": "Sales report",
                "url_name": "admin_mod_report_sales",
                "match": ["admin_mod_report_sales"],
            },
            {
                "label": "Partner production",
                "url_name": "admin_mod_report_partners",
                "match": ["admin_mod_report_partners"],
            },
            {
                "label": "Hotel production",
                "url_name": "admin_mod_report_hotels",
                "match": ["admin_mod_report_hotels"],
            },
            {
                "label": "Cancellation report",
                "url_name": "admin_mod_report_cancellations",
                "match": ["admin_mod_report_cancellations"],
            },
        ],
    },
    {
        "label": "Settings",
        "items": [
            {
                "label": "Nuitee / LiteAPI",
                "url_name": "admin_liteapi_settings",
                "match": ["admin_liteapi_settings"],
            },
            {
                "label": "Currencies & taxes",
                "url_name": "admin_mod_settings_currency",
                "match": ["admin_mod_settings_currency"],
            },
            {
                "label": "Users & roles",
                "url_name": "admin_mod_settings_users",
                "match": ["admin_mod_settings_users"],
            },
            {
                "label": "Email & notifications",
                "url_name": "admin_mod_settings_email",
                "match": ["admin_mod_settings_email"],
            },
            {
                "label": "System admin",
                "url_name": "admin_mod_django_admin",
                "href": "/django-admin/",
                "match": [],
            },
        ],
    },
]

MODULE_PAGES = {
    "admin_mod_direct_hotels": {
        "title": "Direct contract hotels",
        "eyebrow": "Inventory",
        "summary": (
            "Hotels under Magic Sands direct contracts — static allotments, BAR/contract rates, "
            "and priority confirmations outside the Nuitee channel."
        ),
        "bullets": [
            "Hotel master data and board basis",
            "Contract validity windows",
            "Release periods and free-sale flags",
        ],
        "status": "Module scaffold ready",
    },
    "admin_mod_allotments": {
        "title": "Room types & allotments",
        "eyebrow": "Inventory",
        "summary": "Manage room categories, allotment pools, and shared inventory for direct hotels.",
        "bullets": ["Room type catalogue", "Allotment calendars", "Cut-off / release rules"],
        "status": "Module scaffold ready",
    },
    "admin_mod_stopsale": {
        "title": "Stop-sale / close-outs",
        "eyebrow": "Inventory",
        "summary": "Close dates, stop-sell rooms, or restrict channels for direct-contract inventory.",
        "bullets": ["Date-range close-outs", "Room-level stop-sale", "Channel restrictions"],
        "status": "Module scaffold ready",
    },
    "admin_mod_contracts": {
        "title": "Direct contracts",
        "eyebrow": "Rates & contracts",
        "summary": "Store hotel contracts, terms, cancellation policies, and contracted rate sheets.",
        "bullets": ["Contract PDF archive", "Payment terms", "Cancellation & no-show rules"],
        "status": "Module scaffold ready",
    },
    "admin_mod_contract_rates": {
        "title": "Contracted rates",
        "eyebrow": "Rates & contracts",
        "summary": "Seasonal rates, meal plans, child policies, and occupancy pricing for direct hotels.",
        "bullets": ["Season grids", "Meal plan supplements", "Child / extra bed rules"],
        "status": "Module scaffold ready",
    },
    "admin_mod_markups": {
        "title": "Markups & commissions",
        "eyebrow": "Rates & contracts",
        "summary": "B2B markup rules on Nuitee net rates and partner commission structures.",
        "bullets": ["Partner-level markups", "Destination markups", "Commission % tables"],
        "status": "Module scaffold ready",
    },
    "admin_mod_promotions": {
        "title": "Promotions & specials",
        "eyebrow": "Rates & contracts",
        "summary": "Early-bird, stay-pay, and partner-only promotions for direct or channel inventory.",
        "bullets": ["Stay/pay offers", "Blackout dates", "Partner-only flags"],
        "status": "Module scaffold ready",
    },
    "admin_mod_agencies": {
        "title": "Partner agencies",
        "eyebrow": "B2B partners",
        "summary": "Approved agency accounts with login access, markets, and commercial terms.",
        "bullets": ["Approved partner directory", "Account managers", "Market coverage"],
        "cta_label": "Review new registrations",
        "cta_url_name": "partner_requests",
        "status": "Registrations live — agency master next",
    },
    "admin_mod_partner_credit": {
        "title": "Credit & limits",
        "eyebrow": "B2B partners",
        "summary": "Credit limits, payment terms, and booking blocks for B2B agencies.",
        "bullets": ["Credit balance", "Payment due days", "Auto-block on limit"],
        "status": "Module scaffold ready",
    },
    "admin_mod_b2b_rates": {
        "title": "B2B rate plans",
        "eyebrow": "B2B partners",
        "summary": "Partner-specific rate plans combining Nuitee net + markup and direct contracts.",
        "bullets": ["Partner rate sheets", "Inclusive / net display", "Currency defaults"],
        "status": "Module scaffold ready",
    },
    "admin_mod_guests": {
        "title": "Guest profiles",
        "eyebrow": "Guests & CRM",
        "summary": "Guest records from bookings — contact details, nationality, and stay history.",
        "bullets": ["Guest search", "Stay history", "Special requests"],
        "cta_label": "View bookings",
        "cta_url_name": "partner_bookings",
        "status": "Data available via bookings",
    },
    "admin_mod_guest_comms": {
        "title": "Guest communications",
        "eyebrow": "Guests & CRM",
        "summary": "Confirmation, voucher, and reminder email templates for guests and partners.",
        "bullets": ["Booking confirmation", "Voucher PDF email", "Reminder sequences"],
        "status": "Module scaffold ready",
    },
    "admin_mod_invoices": {
        "title": "Invoices",
        "eyebrow": "Finance",
        "summary": "Partner and guest invoices linked to confirmed hotel reservations.",
        "bullets": ["Invoice numbering", "Partner statements", "Tax / VAT lines"],
        "status": "Module scaffold ready",
    },
    "admin_mod_payments": {
        "title": "Payments",
        "eyebrow": "Finance",
        "summary": "Track LiteAPI / Stripe sandbox payments and offline partner settlements.",
        "bullets": ["Card payments", "Bank transfer", "Payment reconciliation"],
        "cta_label": "Pending payment bookings",
        "cta_url_name": "partner_bookings_pending",
        "status": "LiteAPI payment return live",
    },
    "admin_mod_refunds": {
        "title": "Refunds",
        "eyebrow": "Finance",
        "summary": "Process refunds and cancellation penalties for channel and direct bookings.",
        "bullets": ["Refund requests", "Penalty calculation", "Supplier reclaim"],
        "status": "Module scaffold ready",
    },
    "admin_mod_payables": {
        "title": "Supplier payables",
        "eyebrow": "Finance",
        "summary": "Amounts due to Nuitee / hotels under direct contracts after guest stay.",
        "bullets": ["Supplier invoices", "Settlement batches", "FX adjustments"],
        "status": "Module scaffold ready",
    },
    "admin_mod_vouchers": {
        "title": "Vouchers",
        "eyebrow": "Operations",
        "summary": "Hotel vouchers and service vouchers issued after confirmation.",
        "bullets": ["Hotel voucher PDF", "Service voucher", "Reissue / void"],
        "status": "Module scaffold ready",
    },
    "admin_mod_transfers": {
        "title": "Transfers",
        "eyebrow": "Operations",
        "summary": "Airport and intercity transfers packaged with hotel bookings.",
        "bullets": ["Transfer types", "Vehicle allocation", "Driver notes"],
        "status": "Module scaffold ready",
    },
    "admin_mod_extras": {
        "title": "Excursions / extras",
        "eyebrow": "Operations",
        "summary": "Optional tours and add-ons sold with Arabia programmes.",
        "bullets": ["Excursion catalogue", "Pickup points", "Supplier costing"],
        "status": "Module scaffold ready",
    },
    "admin_mod_tickets": {
        "title": "Support tickets",
        "eyebrow": "Operations",
        "summary": "Partner and guest service requests tied to bookings.",
        "bullets": ["Ticket queue", "SLA timers", "Booking linkage"],
        "status": "Module scaffold ready",
    },
    "admin_mod_report_sales": {
        "title": "Sales report",
        "eyebrow": "Reports",
        "summary": "Booking volume, revenue, and conversion across Nuitee and direct inventory.",
        "bullets": ["By date range", "By currency", "By channel"],
        "status": "Module scaffold ready",
    },
    "admin_mod_report_partners": {
        "title": "Partner production",
        "eyebrow": "Reports",
        "summary": "Production and cancellation ratios by B2B agency.",
        "bullets": ["Top partners", "Pending credit", "Market mix"],
        "status": "Module scaffold ready",
    },
    "admin_mod_report_hotels": {
        "title": "Hotel production",
        "eyebrow": "Reports",
        "summary": "Top hotels by room nights for Nuitee and direct-contract properties.",
        "bullets": ["Room nights", "ADR / revenue", "Source mix"],
        "status": "Module scaffold ready",
    },
    "admin_mod_report_cancellations": {
        "title": "Cancellation report",
        "eyebrow": "Reports",
        "summary": "Cancellations, no-shows, and failed payment attempts.",
        "bullets": ["Cancel reasons", "Penalty collected", "Supplier cancel fees"],
        "cta_label": "Open cancellations",
        "cta_url_name": "partner_bookings_cancelled",
        "status": "Linked to booking statuses",
    },
    "admin_mod_settings_currency": {
        "title": "Currencies & taxes",
        "eyebrow": "Settings",
        "summary": "Display currencies, VAT rules, and rounding for invoices and partner rates.",
        "bullets": ["Base currency", "VAT profiles", "Rounding rules"],
        "status": "Module scaffold ready",
    },
    "admin_mod_settings_users": {
        "title": "Users & roles",
        "eyebrow": "Settings",
        "summary": "Staff users for booking ops, finance, and partner management.",
        "bullets": ["Ops / finance roles", "Partner desk", "Audit trail"],
        "cta_label": "Django user admin",
        "cta_href": "/django-admin/auth/user/",
        "status": "Staff login active",
    },
    "admin_mod_settings_email": {
        "title": "Email & notifications",
        "eyebrow": "Settings",
        "summary": "SMTP and notification recipients for partner registration and booking alerts.",
        "bullets": [
            "PARTNER_REGISTRATION_NOTIFY_EMAIL",
            "SMTP host / port",
            "Applicant confirmation templates",
        ],
        "status": "Email hooks live — SMTP configure later",
    },
}
