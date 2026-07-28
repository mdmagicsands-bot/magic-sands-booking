"""Marketing site copy and media sourced from Magic Sands DMC (magicsandsdmc.com)."""

from .assets import ms
from .live_content import (
    HERO_SLIDES,
    HOME_SERVICES,
    LIVE_TESTIMONIALS,
    MEET_US,
    PARTNER_LOGOS,
    VIDEO,
)

TAGLINE = "YOUR GUIDE TO ARABIA"
BRAND = "Magic Sands"
BRAND_FULL = "Magic Sands DMC"
SITE_URL = "https://www.magicsandsdmc.com"


def marketing_page_url(path: str = "/") -> str:
    """Absolute URL to a page on the public marketing website."""
    from django.conf import settings

    base = (getattr(settings, "MARKETING_SITE_URL", None) or SITE_URL).rstrip("/")
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"


MEDIA = {
    "logo": ms("images/logo.png"),
    "favicon": ms("images/favicon.png"),
    "footer_logo": ms("images/footer-logo.png"),
    "about_primary": ms("images/about-2.jpg"),
    "about_secondary": ms("images/about-3.jpg"),
}

HERO_BANNERS = [slide["image"] for slide in HERO_SLIDES]
HERO = {
    "brand": BRAND,
    "title": "Elevating the extraordinary",
    "lede": (
        "At Magic Sands, we design journeys that transcend the expected, "
        "weaving moments of elegance, comfort, and discovery."
    ),
}

ABOUT_BLURB = (
    "Our bespoke services embrace every detail of your travel or event, "
    "ensuring an experience that is seamless, unforgettable, and crafted with care "
    "from the very first step to the last."
)

ABOUT_PAGE = {
    "intro_title": (
        "Our journeys are more than itineraries; they are living stories written "
        "across the canvas of nature’s most captivating scenes"
    ),
    "intro": (
        "We specialize in curating exceptional journeys from the Golden Sands of the Gulf "
        "to the timeless wonders of Jordan and the ancient tales of Egypt."
    ),
    "expertise": (
        "As a premier Destination Management Company, our expertise spans the United Arab Emirates, "
        "Oman, Saudi Arabia, Qatar, Bahrain, Kuwait, Jordan, and Egypt — offering bespoke services "
        "that cater to the sophisticated tastes of our discerning clientele."
    ),
    "story": (
        "Every experience we design is a story in itself — a tale of refinement, comfort, and "
        "unparalleled adventure. Our creative team, with deep local knowledge and a flair for "
        "innovation, works tirelessly to transform your vision into a story worth telling."
    ),
    "boutique_title": "The Boutique Experience",
    "boutique": (
        "Discover the essence of bespoke travel with our boutique experiences — intimate, refined, "
        "and crafted with personal care, where every detail reflects elegance, authenticity, and "
        "exclusivity, and every guest is treated like a seasoned celebrity."
    ),
    "why_title": "Why Choose Magic Sands",
    "why": (
        "At Magic Sands, travel is not just about visiting places — it is about experiencing them "
        "with depth, elegance, and meaning. Clients choose us because we transform journeys into "
        "stories that are as unique as the travelers themselves."
    ),
    "why_detail": (
        "Our expertise lies in creating tailor-made itineraries that reflect your personal vision. "
        "Every detail is designed with precision, from handpicked luxury stays and seamless transfers "
        "to exclusive cultural encounters and hidden gems. With a team rooted in local knowledge and "
        "guided by international standards of service, we open doors to extraordinary moments."
    ),
    "motto": "Orchestrate and elevating the extraordinary experiences",
    "mission": (
        "Craft unforgettable journeys that blend luxury, authenticity, and seamless experiences, "
        "turning every trip into a story worth remembering."
    ),
    "values_intro": (
        "Our passion for crafting exceptional experiences drives everything we do. "
        "We are dedicated to exceeding expectations and delivering excellence at every turn."
    ),
}

DIFFERENTIATORS = [
    {
        "title": "Client-centric relationships",
        "text": (
            "We go beyond transactions to build lasting, personalized connections with every client, "
            "ensuring your unique needs are at the heart of every decision."
        ),
    },
    {
        "title": "Swift response time",
        "text": (
            "Our team is dedicated to providing rapid, efficient service, ensuring every request "
            "is met with prompt and thoughtful solutions, no matter the complexity."
        ),
    },
    {
        "title": "Innovative solutions",
        "text": (
            "We approach every project with creativity and distinction, offering solutions that "
            "elevate your experience and set new standards for excellence."
        ),
    },
    {
        "title": "24/7 tailored support",
        "text": (
            "Our round-the-clock availability means we’re always here for you, delivering bespoke "
            "itineraries and ensuring your journey runs smoothly from start to finish."
        ),
    },
]

VALUES = [
    {
        "title": "Integrity and trust",
        "text": (
            "Integrity and trust form the foundation of every journey we create. We are committed "
            "to transparency, honesty, and ethical practices."
        ),
    },
    {
        "title": "Commitment to partnership",
        "text": (
            "We believe in building strong, long-lasting relationships with our clients, working "
            "together to create truly extraordinary experiences."
        ),
    },
    {
        "title": "Flexibility and adaptability",
        "text": (
            "We understand that every event is unique. Our flexible approach ensures that we can "
            "adapt to any need, offering peace of mind and unparalleled quality."
        ),
    },
    {
        "title": "Collaborative spirit",
        "text": (
            "We believe in the power of teamwork. By working closely with our clients, we ensure "
            "that every project is a success."
        ),
    },
]

ELEVATING = {
    "title": "Elevating the extraordinary",
    "text": (
        "Every journey we craft is a narrative of its own — a harmony of elegance, comfort, and "
        "extraordinary adventure. Our expert team, blending local insight with creative vision, "
        "meticulously transforms your ideas into experiences that linger in memory."
    ),
}

WHY_CHOOSE = [
    {
        "title": "Best rate guarantee",
        "text": "Lowest prices with the best quality and experience.",
        "icon": ms("uploads/pages/facility1.svg"),
    },
    {
        "title": "Diverse destinations",
        "text": "Looking for a unique destination? We have the best across Arabia and beyond.",
        "icon": ms("uploads/pages/facility2.svg"),
    },
    {
        "title": "Free fast booking",
        "text": "Customers can easily book the best tour packages and hotel stays.",
        "icon": ms("uploads/pages/facility3.svg"),
    },
    {
        "title": "Client support 24/7",
        "text": "We provide 24/7 support to our clients and travel partners.",
        "icon": ms("uploads/pages/facility4.svg"),
    },
    {
        "title": "Various adventures",
        "text": "From desert dunes to mountain wadis and coastal escapes — tailored to you.",
        "icon": ms("uploads/pages/facility5.svg"),
    },
    {
        "title": "Best travel guides",
        "text": "Local experts who bring culture, landscape, and hospitality to life.",
        "icon": ms("uploads/pages/facility6.svg"),
    },
]

OFFICES = [
    {
        "label": "Head Office",
        "address": "507, 5th floor, Business center Alkhuwair, Muscat Sultanate of Oman",
        "phone": "+968 9548 1989",
        "email": "info@magicsandsdmc.com",
        "variant": "head",
    },
    {
        "label": "Branch Office (Oman)",
        "address": "Shop #4, 1/2210, Block 415, Al Wafa street, Amerat, Muscat Sultanate of Oman",
        "phone": "+968 9677 2959",
        "email": "oman@magicsandsdmc.com",
        "variant": "branch",
    },
    {
        "label": "Branch Office (UAE)",
        "address": "Building A1, Dubai Digital Park, Dubai Silicon Oasis Dubai, United Arab Emirates",
        "phone": "+971 55 756 1989",
        "email": "uae@magicsandsdmc.com",
        "variant": "branch",
    },
    {
        "label": "Branch Office (Egypt)",
        "address": "Office Number 07, 2 floor, 11 moshtuhur street Cairo downtown, Egypt",
        "phone": "+20111 888 5718",
        "email": "egypt@magicsandsdmc.com",
        "variant": "branch",
    },
    {
        "label": "Branch Office (India)",
        "address": "2nd floor, Hasco Towers, Malampuzha Rd, Chunnambuthara Olavakode, Palakkad, Kerala 678002, India",
        "phone": "+91 6238 784 955",
        "email": "India@magicsandsdmc.com",
        "variant": "branch",
    },
    {
        "label": "Sales Office (Italy)",
        "address": "Ms. Elena Negri Sales Manager – Italian Market Milan, Italy",
        "phone": "+39 366 8744702",
        "email": "italy@magicsandsdmc.com",
        "variant": "branch",
    },
]

CONTACT_BANNER = ms("images/c-banner.jpg")
CONTACT_MAP_EMBED = (
    "https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d914.0616178525753!"
    "2d58.43982400000001!3d23.595492!3m2!1i1024!2i768!4f13.1!3m3!1m2!"
    "1s0x3e91ff17d0672637%3A0x6b9b8607d7da0c98!2sBusiness%20Center%20Al%20Khuwair!"
    "5e0!3m2!1sen!2sin!4v1758959959875!5m2!1sen!2sin"
)

SOCIAL = [
    {"label": "Facebook", "url": "https://www.facebook.com/share/15nCuowwfs/"},
    {"label": "Instagram", "url": "https://www.instagram.com/magicsandsllc"},
    {"label": "LinkedIn", "url": "https://www.linkedin.com/company/magic-sands-dmc/"},
    {"label": "YouTube", "url": "https://www.youtube.com/channel/UCogJAsMh_Nqy11mlw2PPH5g"},
]

DESTINATIONS = [
    {
        "slug": "uae",
        "name": "United Arab Emirates",
        "short": "UAE",
        "summary": (
            "Where golden deserts meet futuristic skylines, ancient traditions embrace "
            "modern luxury, and every moment unfolds as a tapestry of culture, elegance, "
            "and timeless wonder."
        ),
        "teaser": "Experience a dazzling fusion of modern luxury, desert landscapes, and cultural treasures.",
        "image": ms("uploads/destination/d1.jpg"),
        "banner": ms("uploads/banner/banner2.jpg"),
        "accent": "#0f766e",
    },
    {
        "slug": "oman",
        "name": "Oman",
        "short": "Oman",
        "summary": (
            "Where rugged mountains kiss the clouds, golden dunes whisper with the wind, "
            "and turquoise wadis sparkle like hidden jewels — a land where timeless "
            "traditions and serene luxury create memories etched in eternity."
        ),
        "teaser": "Majestic deserts, rugged mountains, pristine beaches, and timeless cultural heritage.",
        "image": ms("uploads/destination/d2.jpg"),
        "banner": ms("uploads/banner/banner3.jpg"),
        "accent": "#b45309",
    },
    {
        "slug": "saudi-arabia",
        "name": "Saudi Arabia",
        "short": "Saudi",
        "summary": (
            "Step into Saudi Arabia, where ancient deserts guard untold stories, Red Sea shores "
            "shimmer with life, and vibrant cities blend heritage with modern grandeur — "
            "a journey of discovery, luxury, and timeless wonder."
        ),
        "teaser": "Discover ancient heritage, vast deserts, modern cities, and sacred cultural treasures.",
        "image": ms("uploads/destination/d3.jpg"),
        "banner": ms("uploads/banner/banner4.jpg"),
        "accent": "#166534",
    },
    {
        "slug": "qatar",
        "name": "Qatar",
        "short": "Qatar",
        "summary": (
            "Explore Qatar, where golden deserts meet gleaming skylines, and rich traditions "
            "blend seamlessly with modern luxury. From bustling souqs to serene seafronts, "
            "every moment unfolds a story of elegance, culture, and unforgettable discovery."
        ),
        "teaser": "Modern skyline, rich culture, desert adventures, and world-class experiences.",
        "image": ms("uploads/destination/d4.jpg"),
        "banner": ms("uploads/banner/banner5.jpg"),
        "accent": "#9f1239",
    },
    {
        "slug": "bahrain",
        "name": "Bahrain",
        "short": "Bahrain",
        "summary": (
            "Experience Bahrain, where serene islands meet modern luxury, and timeless traditions "
            "are woven into every moment. Indulge in refined journeys that linger in memory long "
            "after the sands and seas fade from view."
        ),
        "teaser": "Historic forts, vibrant culture, islands, and modern experiences by the sea.",
        "image": ms("uploads/destination/d5.jpg"),
        "banner": ms("uploads/banner/banner6.jpg"),
        "accent": "#a16207",
    },
    {
        "slug": "kuwait",
        "name": "Kuwait",
        "short": "Kuwait",
        "summary": (
            "Step into Kuwait, a land of historic souqs, majestic mosques, and stories etched in "
            "every street. Immerse yourself in a journey where culture, tradition, and discovery "
            "intertwine seamlessly."
        ),
        "teaser": "Cultural heritage, deserts, islands, and unforgettable Gulf experiences.",
        "image": ms("uploads/destination/d6.jpg"),
        "banner": ms("uploads/banner/banner7.jpg"),
        "accent": "#1d4ed8",
    },
    {
        "slug": "jordan",
        "name": "Jordan",
        "short": "Jordan",
        "summary": (
            "Venture into Jordan, where crimson cliffs of Petra meet the quiet majesty of Wadi Rum, "
            "the Dead Sea glistens under the sun, and every journey is a discovery of timeless "
            "wonder and rich heritage."
        ),
        "teaser": "Timeless deserts and rose-red cities, where history and wonder awaken the soul.",
        "image": ms("uploads/destination/d8.jpg"),
        "banner": ms("uploads/banner/banner8.jpg"),
        "accent": "#be123c",
    },
    {
        "slug": "egypt",
        "name": "Egypt",
        "short": "Egypt",
        "summary": (
            "Explore Egypt’s vast deserts, vibrant cities, and the life-giving Nile. From camel "
            "rides across golden dunes to hidden temples off the beaten path, every journey "
            "promises adventure, wonder, and unforgettable experiences."
        ),
        "teaser": "Sail the Nile, explore ancient pyramids, and awaken your spirit amidst timeless wonders.",
        "image": ms("uploads/destination/d7.jpg"),
        "banner": ms("uploads/banner/1757569372_banner1.jpg"),
        "accent": "#ca8a04",
    },
]

SERVICES = [
    {
        "slug": "travel-leisure",
        "title": "Travel & Leisure",
        "text": (
            "Step into a realm of refined luxury with Magic Sands. Our bespoke travel experiences "
            "are crafted to surpass every expectation — from thrilling adventures to serene escapes."
        ),
        "image": ms("uploads/service/s3.jpg"),
    },
    {
        "slug": "lifestyle",
        "title": "Lifestyle",
        "text": (
            "Take your lifestyle to the next level with personalized experiences that are uniquely "
            "yours. We curate events, culture, and unforgettable moments that let you live life your way."
        ),
        "image": ms("uploads/service/s4.jpg"),
    },
    {
        "slug": "mice",
        "title": "MICE",
        "text": (
            "We design and manage corporate meetings, conferences, and incentive programs with "
            "precision and creativity — inspiring, results-driven events customized to your goals."
        ),
        "image": ms("uploads/service/s5.jpg"),
    },
    {
        "slug": "wellness",
        "title": "Wellness",
        "text": (
            "With Magic Sands, luxury becomes an experience beyond imagination. From thrilling "
            "adventures to tranquil retreats, we craft unforgettable moments designed just for you."
        ),
        "image": ms("uploads/service/s6.jpg"),
    },
    {
        "slug": "concierge",
        "title": "Concierge",
        "text": (
            "Experience the art of effortless living with our concierge service. From securing "
            "coveted dining spots to orchestrating private events, we perfect every detail."
        ),
        "image": ms("uploads/service/s1.jpg"),
    },
    {
        "slug": "csr-sustainability",
        "title": "CSR & Sustainability",
        "text": (
            "We create experiences that are not only extraordinary but also sustainable — "
            "supporting local communities and minimizing environmental impact."
        ),
        "image": ms("uploads/service/s2.jpg"),
    },
]

PARTNERS = [p["image"] for p in PARTNER_LOGOS]

TESTIMONIALS = LIVE_TESTIMONIALS
