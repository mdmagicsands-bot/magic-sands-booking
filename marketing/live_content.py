"""Live-site content extracted from Hostinger htmlbackup + Laravel export."""

from .assets import ms

HERO_SLIDES = [
    {"image": ms("images/banner1.jpg"), "location": "UAE"},
    {"image": ms("images/banner2.jpg"), "location": "Oman"},
    {"image": ms("images/banner3.jpg"), "location": "Saudi"},
    {"image": ms("images/banner4.jpg"), "location": "Qatar"},
    {"image": ms("images/banner5.jpg"), "location": "bahrain"},
    {"image": ms("images/banner6.jpg"), "location": "Kuwait"},
    {"image": ms("images/banner7.jpg"), "location": "Egypt"},
    {"image": ms("images/banner8.jpg"), "location": "Jordan"},
]

HOME_SERVICES = [
    {"title": "Travel & Leisure", "image": ms("uploads/service/s3.jpg"), "col": "7"},
    {"title": "LifeStyle", "image": ms("uploads/service/s4.jpg"), "col": "5"},
    {"title": "Mice", "image": ms("uploads/service/s5.jpg"), "col": "5"},
    {"title": "Wellnes", "image": ms("uploads/service/s6.jpg"), "col": "7"},
    {"title": "Concierge", "image": ms("uploads/service/s1.jpg"), "col": "7"},
    {"title": "CSR & Sustainability", "image": ms("uploads/service/s2.jpg"), "col": "5"},
]

MEET_US = [
    {"image": ms("uploads/client/m1.jpg"), "title": "ATM"},
    {"image": ms("uploads/client/m2.jpg"), "title": "fitur"},
    {"image": ms("uploads/client/m3.png"), "title": "ILTM"},
    {"image": ms("uploads/client/m4.jpg"), "title": "itb"},
    {"image": ms("uploads/client/m5.jpg"), "title": "VIRTUOSO"},
    {"image": ms("uploads/client/m6.jpg"), "title": "WTM"},
]

PARTNER_LOGOS = [
    {"image": ms("uploads/partner/p1.jpg"), "title": "Bahrain Tourism Board"},
    {"image": ms("uploads/partner/p2.jpg"), "title": "Egypt"},
    {"image": ms("uploads/partner/p3.jpg"), "title": "Experience Abu Dhabi"},
    {"image": ms("uploads/partner/p4.png"), "title": "Jordan"},
    {"image": ms("uploads/partner/p5.jpg"), "title": "LTC"},
    {"image": ms("uploads/partner/p6.jpg"), "title": "Saudi"},
    {"image": ms("uploads/partner/p7.jpg"), "title": "Saudi Tourism Authority"},
    {"image": ms("uploads/partner/p8.jpg"), "title": "Dubai"},
]

VIDEO = {
    "image": ms("images/video.jpg"),
    "youtube": "https://www.youtube.com/watch?v=ZZF2qzU7WO4",
}

LIVE_TESTIMONIALS = [
    {
        "name": "George Mcleen",
        "role": "01 Sep 2024 to 02 Sep 2024",
        "rating": 5,
        "image": ms("uploads/testimonial/t1.jpg"),
        "quote": (
            "Amazing place, we had the best time swimming through the wadi and jumping off rocks. "
            "Recommend packing water shoes, cap/hat, and walking trainers — the walk to the water "
            "is uneven and rocky, so don't wear flip flops!!"
        ),
    },
    {
        "name": "Sophia Loren",
        "role": "01 Feb 2024 to 07 Feb 2024",
        "rating": 4,
        "image": ms("uploads/testimonial/t2.jpg"),
        "quote": (
            "Il viaggio è stato fantastico, indulgendo nei luoghi storici vicino ai forti. "
            "Organizzato da Nasser Al Jabri con eccezionali capacità organizzative. Altamente raccomandato."
        ),
    },
    {
        "name": "Riccardo Verdi",
        "role": "01 Apr 2024 to 10 Apr 2024",
        "rating": 5,
        "image": ms("uploads/testimonial/t3.jpg"),
        "quote": (
            "Il nostro tour in Oman è stato a dir poco fantastico! Dalle meravigliose dune di sabbia "
            "di Wahiba Sands alla serena bellezza di Wadi Shab, ogni parte del viaggio è stata una nuova avventura."
        ),
    },
    {
        "name": "Jessica Silotti",
        "role": "12 Aug 2024 to 19 Aug 2024",
        "rating": 5,
        "image": ms("uploads/testimonial/default.png"),
        "quote": "Un eccellente organizzazione ed una guida fantastica. Sicuramente li contatterò per altri viaggi",
    },
    {
        "name": "Chaimaa Labe",
        "role": "18 Aug 2025 to 18 Aug 2025",
        "rating": 5,
        "image": ms("uploads/testimonial/default.png"),
        "quote": (
            "Tour di Muscate bellissimo. La nostra guida Ossama (e autista) il migliore! Preparatissimo, "
            "gentile e sempre disponibile. Consigliatissimo!"
        ),
    },
    {
        "name": "Laita Fiorese",
        "role": "11 Aug 2025 to 11 Aug 2025",
        "rating": 5,
        "image": ms("uploads/testimonial/default.png"),
        "quote": (
            "During a long stepover in Muscat we decided to do a guided tour. Osama drove us around the city, "
            "we saw beautiful places, and he explained the history and traditions. I absolutely recommend him!"
        ),
    },
    {
        "name": "Fernando Carioni",
        "role": "11 Apr 2025 to 21 Apr 2025",
        "rating": 5,
        "image": ms("uploads/testimonial/default.png"),
        "quote": "We have spent a wondurfull time with Osama. Now we know many things about people and history of Oman.",
    },
    {
        "name": "Elena Verga",
        "role": "12 Apr 2025 to 21 Apr 2025",
        "rating": 5,
        "image": ms("uploads/testimonial/default.png"),
        "quote": (
            "Very good experience! Fantastic tour with Magic Sands a special thank to the great guide Osama!! "
            "I would like to come back to Oman and contact Magic Sands to organize my trip!"
        ),
    },
    {
        "name": "Gaibazzi Giorgio",
        "role": "07 Dec 2024 to 17 Dec 2024",
        "rating": 5,
        "image": ms("uploads/testimonial/default.png"),
        "quote": (
            "Viaggio meraviglioso e molto ben organizzato. Paesaggi stupendi, ospitalità e cordialità. "
            "La guida parlava molto bene italiano ed era colta e preparata."
        ),
    },
    {
        "name": "Lisa Colucci",
        "role": "12 Sep 2023 to 16 Sep 2023",
        "rating": 5,
        "image": ms("uploads/testimonial/default.png"),
        "quote": (
            "Una guida eccezionale e un viaggio indimenticabile! Ossama conosce ogni aspetto dell'Oman — "
            "dalla cultura alla natura, dalla storia alla vita della gente locale."
        ),
    },
]
