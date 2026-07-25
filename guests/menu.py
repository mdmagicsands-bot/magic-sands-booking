"""Left navigation for the guest Nuitee-style booking portal."""

GUEST_MENU = [
    {
        "label": "Main",
        "items": [
            {
                "label": "Dashboard",
                "url_name": "guest_dashboard",
                "match": ["guest_dashboard"],
            },
            {
                "label": "Hotel search",
                "url_name": "guest_search",
                "match": ["guest_search", "guest_search_results"],
            },
            {
                "label": "My bookings",
                "url_name": "guest_bookings",
                "match": ["guest_bookings", "guest_booking_detail"],
            },
        ],
    },
    {
        "label": "Account",
        "items": [
            {
                "label": "Saved hotels",
                "url_name": "guest_saved",
                "match": ["guest_saved"],
            },
            {
                "label": "Profile",
                "url_name": "guest_profile",
                "match": ["guest_profile"],
            },
            {
                "label": "Help & support",
                "url_name": "guest_support",
                "match": ["guest_support"],
            },
        ],
    },
]
