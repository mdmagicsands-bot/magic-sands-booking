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

# Full guest reviews from Hostinger htmlbackup testimonials.php
LIVE_TESTIMONIALS = [
    {
        "name": "Nouaim Hadri",
        "role": "7–14 May 2026",
        "rating": 5,
        "image": ms("uploads/testimonial/2524b85e_c622_4e84_9041_90d97c5ea4a8.jpeg"),
        "image_path": "uploads/testimonial/2524b85e_c622_4e84_9041_90d97c5ea4a8.jpeg",
        "quote": "Amazing trip in Oman from Muscat City, different wadis, desert, Jebel Akhdar and finally to Al Bandar. Magic Sands organised everything to be comfortable on our trip.",
    },
    {
        "name": "George Mcleen",
        "role": "01 Sep 2024 to 02 Sep 2024",
        "rating": 5,
        "image": ms("uploads/testimonial/t1.jpg"),
        "image_path": "uploads/testimonial/t1.jpg",
        "quote": "Amazing place, we had the best time swimming through the wadi and jumping off rocks. So much fun and our group of people was great. I would just suggest you hire a car/ taxi and do it yourself. If you research before it would be easy enough to do.\n\nRecommend packing water shoes, cap/ hat, top all for swimming as you're exposed to the sun throughout swimming and walking. Very hot over 40 in June so I walked in a long sleeve top and shorts then swam in them as it's a real pain/ dusty/ hot trying to change out there. Walking trainers/ boots are needed too as the 40min walk to the water is uneven and rocky so don't wear flip flops!!",
    },
    {
        "name": "Antonio Losi",
        "role": "26 Dec 2025 – 4 Jan 2026",
        "rating": 5,
        "image": ms("uploads/testimonial/IMG_20251116_WA0025.jpg"),
        "image_path": "uploads/testimonial/IMG_20251116_WA0025.jpg",
        "quote": "The trip was truly perfect. Everything went exactly as planned. There were 11 of us, and every single person was genuinely happy. Thank you, friends at Magic Sands.",
    },
    {
        "name": "Sophia Loren",
        "role": "01 Feb 2024 to 07 Feb 2024",
        "rating": 4,
        "image": ms("uploads/testimonial/t2.jpg"),
        "image_path": "uploads/testimonial/t2.jpg",
        "quote": "Il viaggio è stato fantastico, indulgendo nei luoghi storici vicino ai forti. Sono stato con amici per una breve vacanza con una compagnia di guide turistiche esperte dell'Oman, organizzata da una compagnia di tour di montagna. Il viaggio è stato organizzato dal tour operator Nasser Al Jabri con eccezionali capacità organizzative e gestionali. Altamente raccomandato per te",
    },
    {
        "name": "Riccardo Pasquotti",
        "role": "6–11 Dec 2025",
        "rating": 5,
        "image": ms("uploads/testimonial/20260222_172738.jpg"),
        "image_path": "uploads/testimonial/20260222_172738.jpg",
        "quote": "We had an amazing experience in Oman. Our guide, Osama, was impeccable. His knowledge and connection with local people made our trip unique.",
    },
    {
        "name": "Riccardo Verdi",
        "role": "01 Apr 2024 to 10 Apr 2024",
        "rating": 5,
        "image": ms("uploads/testimonial/t3.jpg"),
        "image_path": "uploads/testimonial/t3.jpg",
        "quote": "\"Un viaggio indimenticabile!\"\n\"Il nostro tour in Oman è stato a dir poco fantastico! Dalle meravigliose dune di sabbia di Wahiba Sands alla serena bellezza di Wadi Shab, ogni parte del viaggio è stata una nuova avventura. La nostra guida era molto ben informata e ha reso l'esperienza ancora più speciale. Consiglio vivamente questo tour a chiunque desideri esplorare le gemme nascoste dell'Oman.\"",
    },
    {
        "name": "Simon Beltrami",
        "role": "21–29 Nov 2025",
        "rating": 5,
        "image": ms("uploads/testimonial/IMG_4412.jpeg"),
        "image_path": "uploads/testimonial/IMG_4412.jpeg",
        "quote": "Everything was perfect — transfers and assistance. When we needed to change a hotel room they helped immediately. Punctual and professional.",
    },
    {
        "name": "Jessica Silotti",
        "role": "12 Aug 2024 to 19 Aug 2024",
        "rating": 5,
        "image": ms("uploads/testimonial/t4.png"),
        "image_path": "uploads/testimonial/t4.png",
        "quote": "Un eccellente organizzazione ed una guida fantastica. Sicuramente li contatterò per altri viaggi",
    },
    {
        "name": "Alessia Gasco",
        "role": "11–17 Nov 2025",
        "rating": 5,
        "image": ms("uploads/testimonial/c2343ee8_503f_4fa5_978f_ec5bad6d86c9.jpeg"),
        "image_path": "uploads/testimonial/c2343ee8_503f_4fa5_978f_ec5bad6d86c9.jpeg",
        "quote": "We had such a great time in Oman! Hossam was an absolute star — fun, knowledgeable, and constantly going the extra mile to make sure everyone was happy and safe.",
    },
    {
        "name": "Chaimaa Labe",
        "role": "18 Aug 2025 to 18 Aug 2025",
        "rating": 5,
        "image": ms("uploads/testimonial/20260511_053705.jpg"),
        "image_path": "uploads/testimonial/20260511_053705.jpg",
        "quote": "Tour di Muscate bellissimo. La nostra guida Ossama (e autista) il migliore! Preparatissimo, gentile e sempre disponibile. Ci ha fatto scoprire luoghi incredibili con passione e competenza, raccontandoci la storia e la cultura dell'Oman in modo coinvolgente e mai noioso. Grazie a lui, l'esperienza è stata davvero indimenticabile. Consigliatissimo!",
    },
    {
        "name": "Laita Fiorese",
        "role": "11 Aug 2025 to 11 Aug 2025",
        "rating": 5,
        "image": ms("uploads/testimonial/IMG_2536.jpeg"),
        "image_path": "uploads/testimonial/IMG_2536.jpeg",
        "quote": "During a long stepover in Muscat we decided to do a guided tour. Osama drove us around the city, we saw a lot of beautiful places and he explained us everything about the history and the tradition of the Omani. I absolutely recommend him!",
    },
    {
        "name": "Fernando Carioni",
        "role": "11 Apr 2025 to 21 Apr 2025",
        "rating": 5,
        "image": ms("uploads/testimonial/8f000809_8302_4d3b_9ec0_fd131fd9fac4.jpeg"),
        "image_path": "uploads/testimonial/8f000809_8302_4d3b_9ec0_fd131fd9fac4.jpeg",
        "quote": "We have spent a wondurfull time with Osama. Now we know many things about people and history of Oman. Thanks a lot Osama for your time.",
    },
    {
        "name": "Elena Verga",
        "role": "12 Apr 2025 to 21 Apr 2025",
        "rating": 5,
        "image": ms("uploads/testimonial/3cfc57e0_cc23_4dc8_9f5f_dabd9682dee1.jpeg"),
        "image_path": "uploads/testimonial/3cfc57e0_cc23_4dc8_9f5f_dabd9682dee1.jpeg",
        "quote": "Very good experience! Fantastic tour with Magic Sands a special thank to the great guide Osama !! I would like to come back to Oman and of course I will contact Magic Sands to organize my trip!",
    },
    {
        "name": "Marusca Cantaluppi",
        "role": "6–13 Feb 2026",
        "rating": 5,
        "image": ms("uploads/testimonial/IMG_4943.jpeg"),
        "image_path": "uploads/testimonial/IMG_4943.jpeg",
        "quote": "Abdullah è stato molto gentile, sempre disponibile, molto bravo a guidare e a risolvere gli imprevisti durante il viaggio.",
    },
    {
        "name": "Lorenzo Rossi",
        "role": "7–13 Feb 2026",
        "rating": 5,
        "image": ms("uploads/testimonial/IMG_1861.jpeg"),
        "image_path": "uploads/testimonial/IMG_1861.jpeg",
        "quote": "Everything was fine! Abdullah was a perfect driver and a very good guide for all aspects of Omani treasures.",
    },
    {
        "name": "Gaibazzi Giorgio",
        "role": "07 Dec 2024 to 17 Dec 2024",
        "rating": 5,
        "image": ms("uploads/testimonial/IMG_3499.jpeg"),
        "image_path": "uploads/testimonial/IMG_3499.jpeg",
        "quote": "Io e Costanza abbiamo fatto un viaggio meraviglioso e molto ben organizzato. Paesaggi stupendi, ospitalità e cordialità. La guida, che parlava molto bene italiano, era colta e preparata su tutti gli argomenti. Grazie per averci fatto vivere una vacanza indimenticabile !",
    },
    {
        "name": "Lisa Colucci",
        "role": "12 Sep 2023 to 16 Sep 2023",
        "rating": 5,
        "image": ms("uploads/testimonial/d52b9197_f1bb_47d2_89c6_7a626fe57165.jpeg"),
        "image_path": "uploads/testimonial/d52b9197_f1bb_47d2_89c6_7a626fe57165.jpeg",
        "quote": "Una guida eccezionale e un viaggio indimenticabile! Abbiamo avuto la fortuna di avere Ossama come guida durante il nostro viaggio in Oman, ed è stata un'esperienza fantastica! Ossama è una persona incredibile, gentile, competente e sempre disponibile. Conosce ogni aspetto dell'Oman: dalla cultura alla natura, dalla storia alla vita della gente locale. Non importa quale fosse la nostra domanda, lui aveva sempre una risposta o un suggerimento. Il viaggio è stato pianificato con grande cura e attenzione ai nostri desideri. Ossama è riuscito a includere tutto ciò che volevamo vedere e ci ha sorpreso con tantissimi altri luoghi e attività lungo il percorso, rendendo il nostro road trip ancora più speciale. Abbiamo vissuto momenti indimenticabili: dal deserto ai magnifici wadi, dalle spiagge paradisiache alla Grande Moschea di Muscat e alla città vecchia. Ossama ci ha mostrato tutto con",
    },
    {
        "name": "Oscar Cicchetti",
        "role": "7–11 Feb 2026",
        "rating": 5,
        "image": ms("uploads/testimonial/default.png"),
        "image_path": "uploads/testimonial/default.png",
        "quote": "Great trip. Sahid has been an excellent guide.",
    },
]
