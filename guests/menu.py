"""Top navigation for the Magic Sands partner booking portal."""

GUEST_MENU = [
    {
        "label": "Search",
        "url_name": "guest_search",
        "match": ["guest_search", "guest_search_results"],
    },
    {
        "label": "My Bookings",
        "url_name": "guest_bookings",
        "match": ["guest_bookings", "guest_booking_detail"],
    },
    {
        "label": "Quotation",
        "match": [],
        "placeholder": True,
    },
    {
        "label": "User Management",
        "match": ["guest_profile", "guest_saved"],
        "children": [
            {
                "label": "Profile",
                "url_name": "guest_profile",
                "match": ["guest_profile"],
            },
            {
                "label": "Saved hotels",
                "url_name": "guest_saved",
                "match": ["guest_saved"],
            },
        ],
    },
    {
        "label": "More",
        "match": ["guest_support"],
        "children": [
            {
                "label": "Help & support",
                "url_name": "guest_support",
                "match": ["guest_support"],
            },
        ],
    },
    {
        "label": "Dashboard",
        "url_name": "guest_dashboard",
        "match": ["guest_dashboard"],
    },
]
