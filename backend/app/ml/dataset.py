"""
Labeled fake review dataset for training the classifier.

Based on patterns from Ott et al. (2011) "Finding Deceptive Opinion Spam
by Any Stretch of the Imagination" and extended with e-commerce-specific
patterns observed on Flipkart/Amazon.

Labels:  1 = fake/deceptive,  0 = genuine/truthful

Features used for classification:
  - Text content (TF-IDF)
  - Review length
  - Rating extremity
  - Exclamation count
  - Caps ratio
  - Contains URL
  - Generic phrase count
"""

LABELED_REVIEWS = [
    # ──────────────── GENUINE POSITIVE REVIEWS (label=0) ────────────────
    {
        "text": "I've been using this phone for about 3 months now. The camera quality is genuinely impressive, "
                "especially in daylight conditions. Night mode is decent but not as good as the Pixel. Battery "
                "lasts me about 6-7 hours of screen-on time which is acceptable. The only complaint I have is "
                "that the fingerprint sensor is a bit slow sometimes. Overall, I think it's a good phone for "
                "the price, but not the best in this range.",
        "rating": 4, "verified": True, "label": 0
    },
    {
        "text": "Bought this for my mother's birthday. She loves the large display and the font size options. "
                "Call quality is clear and the speaker volume is loud enough for her. Setting up was a bit "
                "tricky as I had to transfer her WhatsApp data. The phone does get warm during charging but "
                "nothing alarming. For a budget phone, this checks most boxes.",
        "rating": 4, "verified": True, "label": 0
    },
    {
        "text": "Coming from a Samsung S20, this is a noticeable upgrade in terms of display quality and "
                "refresh rate. The 120Hz panel is buttery smooth. However, I found the haptics to be weaker "
                "than my old Samsung. The charging speed is fantastic though - 0 to 80% in about 30 minutes. "
                "Software experience is clean with minimal bloatware.",
        "rating": 4, "verified": True, "label": 0
    },
    {
        "text": "The build quality is premium and feels solid in hand. I dropped it once from about 3 feet "
                "and the screen protector saved it but got a small dent on the corner. Camera takes great "
                "photos during the day. Night photos are average. Battery is good, lasts a full day with "
                "moderate usage. Charging is fast. One issue - the proximity sensor acts weird during calls.",
        "rating": 4, "verified": True, "label": 0
    },
    {
        "text": "Display is vibrant and sharp. I watch a lot of YouTube and Netflix on this and the "
                "experience is great with the stereo speakers. Gaming performance is smooth for most games "
                "but BGMI on max settings causes some frame drops after 20 minutes. The phone heats up "
                "during gaming but stays cool for normal use. Decent phone for the price.",
        "rating": 3, "verified": True, "label": 0
    },
    {
        "text": "After using this laptop for 2 weeks, here's my honest take. The keyboard is comfortable "
                "for typing long documents. The trackpad is responsive. However, the display could have been "
                "brighter - I struggle to see in direct sunlight. Fan noise is noticeable under load. For "
                "office work and light photo editing, it's perfectly fine. Don't expect gaming performance.",
        "rating": 3, "verified": True, "label": 0
    },
    {
        "text": "The washing machine works well for daily loads. We're a family of four and it handles "
                "our laundry efficiently. The quick wash mode is a lifesaver for lightly soiled clothes. "
                "Installation was done by the company within 2 days. However, it's a bit noisy during "
                "the spin cycle. Energy consumption seems reasonable based on our last electricity bill.",
        "rating": 4, "verified": True, "label": 0
    },
    {
        "text": "I bought this mixer grinder to replace my old one. The motor is powerful and grinds "
                "even hard spices smoothly. The jars are sturdy. However, the locking mechanism is a bit "
                "stiff and takes some getting used to. Also the cord is shorter than I'd like. The noise "
                "level is standard for this type of appliance. Works well for Indian cooking needs.",
        "rating": 4, "verified": True, "label": 0
    },
    {
        "text": "Received the headphones yesterday. Sound quality is balanced with decent bass. Not "
                "audiophile-grade but perfectly fine for casual listening and calls. ANC works well in "
                "office environments but doesn't fully block out loud traffic noise. Comfort is good - "
                "I wore them for 4 hours straight without ear fatigue. Battery life matches the claim of "
                "about 25 hours. App has useful EQ settings.",
        "rating": 4, "verified": True, "label": 0
    },
    {
        "text": "The smartwatch tracks steps and heart rate reasonably accurately when compared to my "
                "gym's equipment. Sleep tracking is hit or miss - sometimes it doesn't register naps. The "
                "UI is responsive but limited in terms of watch faces. Notifications from phone come through "
                "reliably. Battery lasts about 5 days with always-on display off. Good entry-level smartwatch.",
        "rating": 3, "verified": True, "label": 0
    },
    {
        "text": "I've had this refrigerator for 6 months now. Cooling is consistent and the inverter "
                "compressor keeps electricity bills low. The vegetable crisper keeps things fresh for about "
                "a week. The freezer section is spacious. My only gripe is that the door shelves are a bit "
                "shallow for larger bottles. Overall, satisfied with the purchase for this price range.",
        "rating": 4, "verified": True, "label": 0
    },
    {
        "text": "This is my third pair of these running shoes. The cushioning is still excellent and "
                "they provide great support for my flat feet. I run about 30km per week and these have "
                "lasted me nearly 6 months each time. The mesh upper breathes well. Sizing runs true to "
                "size. The only downside is limited color options compared to Nike.",
        "rating": 5, "verified": True, "label": 0
    },
    {
        "text": "The air purifier works quietly on the low setting and the air quality indicator is "
                "helpful. I have allergies and noticed a difference within the first week of use. The "
                "filter replacement is reasonably priced. My room is about 250 sqft and it handles it "
                "well. On the highest setting it's audible but not bothersome. Power consumption is around "
                "40 watts which is acceptable.",
        "rating": 4, "verified": True, "label": 0
    },
    {
        "text": "Used this trimmer for 3 weeks now. The blade is sharp and gives a clean trim. Battery "
                "lasts for about 4-5 uses on a full charge, which is less than the advertised 90 minutes. "
                "The travel lock is a nice feature. Comes with multiple guard attachments. The build feels "
                "plastic-y but functional. For the price, can't really complain.",
        "rating": 3, "verified": True, "label": 0
    },
    {
        "text": "The tablet is great for reading ebooks and browsing. The display is sharp with good "
                "viewing angles. However, it struggles with heavy multitasking and some apps take a "
                "moment to load. Speaker quality is just okay - I use bluetooth headphones mostly. "
                "The included stylus is a nice touch for note-taking. Battery easily lasts 8-9 hours.",
        "rating": 4, "verified": True, "label": 0
    },

    # ──────────────── GENUINE NEGATIVE REVIEWS (label=0) ────────────────
    {
        "text": "Disappointed with this purchase. The phone started lagging within a month of use. Apps "
                "take forever to open and the UI stutters when switching between apps. I tried factory "
                "reset but the problem persists. Battery drain is also excessive - barely lasts 4 hours "
                "with normal use. I have contacted service center and they said it's a software issue that "
                "will be fixed in next update. Still waiting after 3 weeks.",
        "rating": 2, "verified": True, "label": 0
    },
    {
        "text": "The vacuum cleaner stopped working after just 2 months. The suction power was good "
                "initially but gradually decreased. The filter gets clogged very quickly even with regular "
                "cleaning. Customer service was unhelpful - they kept asking me to send videos of the issue. "
                "After multiple follow-ups they finally agreed to a replacement but it's been 2 weeks and "
                "nothing has arrived. Very frustrating experience.",
        "rating": 1, "verified": True, "label": 0
    },
    {
        "text": "Received a defective unit. The screen had a noticeable yellow tint on one side. Tried "
                "adjusting display settings but couldn't fix it. Returned it and the replacement had "
                "a similar issue though slightly less pronounced. Beginning to think this is a widespread "
                "quality control issue. The phone is otherwise decent but I can't ignore a display defect "
                "on a phone I'm paying 25K for.",
        "rating": 2, "verified": True, "label": 0
    },
    {
        "text": "The chair arrived with a scratched armrest and one wheel that doesn't roll properly. "
                "Assembly instructions were confusing and the allen key provided was too small for some "
                "bolts. The cushion is firm which some might like but I find uncomfortable after sitting "
                "for more than an hour. Lumbar support adjustment barely makes a difference. Expected "
                "better quality for the price.",
        "rating": 2, "verified": True, "label": 0
    },
    {
        "text": "This iron stopped heating after about 45 days of use. It was working fine initially "
                "but then the steam function failed first, followed by the heating element. Since it was "
                "past the 30-day return window, I had to go through warranty. The service center took "
                "10 days to repair it and it stopped working again after a week. Clearly a manufacturing "
                "defect. Won't recommend this brand.",
        "rating": 1, "verified": True, "label": 0
    },
    {
        "text": "Delivery was terrible. Ordered on sale day and it took 12 days to arrive despite the "
                "promised 3-day delivery. The packaging was damaged and the product box was dented. "
                "Fortunately the product itself seems fine so far, but the experience leaves a bad taste. "
                "The tracking showed it sitting at a hub for 5 days with no updates.",
        "rating": 2, "verified": True, "label": 0
    },
    {
        "text": "Not worth the hype. The noise cancellation is mediocre at best. I can still hear my "
                "AC running and people talking nearby. Call quality is terrible too - people on the other "
                "end complain they can barely hear me. The only redeeming quality is comfort. For this "
                "price there are much better options available from brands like Sony or Sennheiser.",
        "rating": 2, "verified": True, "label": 0
    },
    {
        "text": "Major heating issue with this laptop. During video calls it reaches over 90 degrees "
                "and the fan sounds like a jet engine. I have to use a cooling pad just for basic tasks. "
                "Performance is fine when it's cool but thermal throttling kicks in during any sustained "
                "workload. Also the webcam quality is poor - looks like a 2010 camera. Considering "
                "returning this and getting a MacBook Air instead.",
        "rating": 2, "verified": True, "label": 0
    },
    {
        "text": "Color is completely different from what was shown in the pictures. The listing showed "
                "a vibrant blue but what I received is more like a dull navy. The material feels cheap "
                "and thin. Stitching is already coming loose near the collar after just one wash. The "
                "sizing is also off - I ordered L based on the chart but it fits like an XL. Very "
                "misleading listing.",
        "rating": 1, "verified": True, "label": 0
    },
    {
        "text": "The power bank capacity is nowhere near what's advertised. They claim 20000mAh but "
                "I can barely charge my phone (4500mAh battery) twice. That's a conversion efficiency "
                "of less than 50% which is unacceptable. The LED indicators are also unreliable - it "
                "shows 2 bars when it's actually almost empty. At least the charging speed is decent.",
        "rating": 2, "verified": True, "label": 0
    },

    # ──────────────── FAKE POSITIVE REVIEWS (label=1) ────────────────
    {
        "text": "Best product ever!! Amazing quality, must buy for everyone!!! You won't regret it!!!",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "Excellent excellent excellent! This is the best phone in the world. Five stars. "
                "Everyone should buy this. Best purchase of my life.",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "Amazing product. Super quality. Fast delivery. Best seller. Highly recommended. "
                "Five stars. Will buy again.",
        "rating": 5, "verified": True, "label": 1
    },
    {
        "text": "WOW JUST WOW! THIS IS THE BEST THING I HAVE EVER BOUGHT IN MY ENTIRE LIFE!!! "
                "ABSOLUTELY FANTASTIC PRODUCT!!!",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "Good product good quality good price good everything.",
        "rating": 5, "verified": True, "label": 1
    },
    {
        "text": "Nice nice nice. Very nice product. Must buy. Buy it now. Best deal ever.",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "Five star product. Best in class. Premium quality. Value for money. Superb.",
        "rating": 5, "verified": True, "label": 1
    },
    {
        "text": "I am very happy with this product the seller is very good and the product is very "
                "good and the quality is very good and the price is very good I recommend everyone to "
                "buy this product from this seller.",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "Perfect product! A+++ seller! Fast shipping! Will buy again! Highly recommended to all!",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "Just amazing. No words. Best phone. Best camera. Best battery. Best everything. "
                "Simply the best. Period.",
        "rating": 5, "verified": True, "label": 1
    },
    {
        "text": "Love love love this product! It changed my life! Everyone needs one! Buy it NOW!",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "Superb product very nice quality I am loving it thanks flipkart for such a nice "
                "product will buy more products from this seller.",
        "rating": 5, "verified": True, "label": 1
    },
    {
        "text": "Excellent product excellent delivery excellent packaging excellent everything!!!!",
        "rating": 5, "verified": True, "label": 1
    },
    {
        "text": "This product is just awesome amazing fantastic superb extraordinary! Best purchase!",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "HIGHLY RECOMMEND THIS TO EVERYONE. BEST PRODUCT. FIVE STARS. A MUST BUY.",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "Very good product. Received on time. Nice packaging. Product as described. Happy "
                "with purchase. Thank you seller.",
        "rating": 5, "verified": True, "label": 1
    },
    {
        "text": "This phone is incredible!!! Best camera ever seen!!! Battery lasts a whole week!!! "
                "Best phone in the universe!!! Don't think just buy it!!!",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "Outstanding product! The seller deserves 10 stars! Best experience ever! Will "
                "definitely buy from this seller again!",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "Simply superb. No complaints. Everything perfect. 10/10 would recommend. "
                "Buy buy buy. You won't find anything better.",
        "rating": 5, "verified": True, "label": 1
    },
    {
        "text": "Best quality. Premium finish. Awesome phone. Great camera. Long battery. "
                "Fast charging. Perfect display. Just buy it.",
        "rating": 5, "verified": True, "label": 1
    },

    # ──────────────── FAKE NEGATIVE REVIEWS (label=1) ────────────────
    {
        "text": "WORST PRODUCT EVER! DO NOT BUY! COMPLETE WASTE OF MONEY!!!",
        "rating": 1, "verified": False, "label": 1
    },
    {
        "text": "Terrible terrible terrible. Don't waste your money on this garbage.",
        "rating": 1, "verified": False, "label": 1
    },
    {
        "text": "Don't buy this product. It is very bad. Worst quality. Waste of money. "
                "Zero stars if I could.",
        "rating": 1, "verified": False, "label": 1
    },
    {
        "text": "Fraud fraud fraud! This seller is a cheater! Product is fake! Report this listing!",
        "rating": 1, "verified": False, "label": 1
    },
    {
        "text": "Horrible product. Broke on day one. Complete junk. Save your money. "
                "Pathetic quality.",
        "rating": 1, "verified": True, "label": 1
    },
    {
        "text": "SCAM ALERT!!! This is not the original product!!! FAKE FAKE FAKE!!! "
                "DO NOT ORDER FROM THIS SELLER!!!",
        "rating": 1, "verified": False, "label": 1
    },
    {
        "text": "Very bad product. Worst purchase ever. Money wasted. Don't buy. One star.",
        "rating": 1, "verified": False, "label": 1
    },
    {
        "text": "Useless product useless seller useless service. Total disaster.",
        "rating": 1, "verified": False, "label": 1
    },
    {
        "text": "AVOID THIS PRODUCT AT ALL COSTS. WORST THING I HAVE EVER PURCHASED.",
        "rating": 1, "verified": False, "label": 1
    },
    {
        "text": "Received broken product. Seller is fraud. Don't trust. Report immediately. "
                "Waste of hard earned money.",
        "rating": 1, "verified": False, "label": 1
    },

    # ──────────────── MORE GENUINE REVIEWS (label=0) ────────────────
    {
        "text": "For the price point this is reasonable. The fabric is soft and comfortable "
                "for daily wear. Colors haven't faded after 5 washes. But the fitting is slightly "
                "loose around the shoulders. I'd suggest ordering one size down if you prefer a "
                "fitted look. Decent for casual wear.",
        "rating": 3, "verified": True, "label": 0
    },
    {
        "text": "The keyboard has a satisfying tactile feel. I'm a programmer and type around "
                "8 hours daily - no fatigue issues so far after 2 months. The RGB lighting is a nice "
                "bonus though not essential for me. Software for macro programming is a bit clunky "
                "but works. Build feels solid. Would have preferred a detachable USB cable.",
        "rating": 4, "verified": True, "label": 0
    },
    {
        "text": "Decent monitor for the price. Colors are accurate enough for casual photo "
                "editing. The 75Hz refresh rate is a minor upgrade over 60Hz and I can notice the "
                "difference when scrolling. Viewing angles are okay but colors shift noticeably at "
                "extreme angles. Stand is basic and doesn't offer height adjustment - I use a "
                "monitor arm instead.",
        "rating": 3, "verified": True, "label": 0
    },
    {
        "text": "I've been cooking with this pressure cooker for 2 months. It heats evenly and "
                "the whistle timing is consistent. The handles stay cool which is a safety plus. "
                "Cleaned up easily. The gasket seems durable but I'll update after 6 months. "
                "Capacity is perfect for a family of 3-4. Slightly heavy though.",
        "rating": 4, "verified": True, "label": 0
    },
    {
        "text": "This mattress improved my sleep quality noticeably. The medium-firm feel supports "
                "my back well - I have mild disc issues and my physiotherapist recommended something "
                "like this. It took about a week to fully expand after unboxing. There is a slight "
                "chemical smell initially that goes away within 2-3 days.",
        "rating": 4, "verified": True, "label": 0
    },
    {
        "text": "The camera quality is actually decent for a phone in this budget. Daylight shots "
                "are sharp with natural colors. Portrait mode is hit or miss - sometimes the edge "
                "detection messes up around hair. Video stabilization works for walking but not great "
                "for running. No 4K support which is expected at this price.",
        "rating": 3, "verified": True, "label": 0
    },
    {
        "text": "Mixed feelings about this purchase. The design is definitely eye-catching and "
                "I get compliments. But practically, the battery life is below average at about "
                "4.5 hours screen time. Also the speaker placement at the bottom means it gets "
                "muffled when I hold it in landscape for videos. Software is clean though.",
        "rating": 3, "verified": True, "label": 0
    },
    {
        "text": "Does exactly what it says. Nothing more, nothing less. The fan moves a decent "
                "amount of air and the three speed settings are useful. It's relatively quiet on "
                "low and medium settings. The oscillation covers a good range. Build quality is "
                "average plastic. For a basic fan at this price, it's fine.",
        "rating": 3, "verified": True, "label": 0
    },
    {
        "text": "Bought this router to extend my WiFi to the second floor. Speed throughput is "
                "good - I get about 80% of my plan speed on the upper floor now, up from barely "
                "30%. Setup was straightforward using the app. The only issue is occasional "
                "disconnections that require a reboot, happening maybe once a week.",
        "rating": 4, "verified": True, "label": 0
    },
    {
        "text": "Installed this dashcam last week. Day recording quality is excellent with clear "
                "number plates. Night quality is usable but grainy. The suction mount holds firmly. "
                "Parking mode is a nice feature though it drains the battery after about 8 hours. "
                "Loop recording works as expected. The app for viewing footage is basic but functional.",
        "rating": 4, "verified": True, "label": 0
    },

    # ──────────────── MORE FAKE/SPAM REVIEWS (label=1) ────────────────
    {
        "text": "Buy from this seller only. Best seller on flipkart. All other sellers are fraud. "
                "Go for it blindly. You won't be disappointed I promise.",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "This product is God level amazing!! The technology used in this product is truly "
                "revolutionary!! It's light years ahead of any competition in the market!!",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "Good",
        "rating": 5, "verified": True, "label": 1
    },
    {
        "text": "Nice product",
        "rating": 5, "verified": True, "label": 1
    },
    {
        "text": "Superb",
        "rating": 5, "verified": True, "label": 1
    },
    {
        "text": "Ok",
        "rating": 3, "verified": True, "label": 1
    },
    {
        "text": "Worst. Pathetic. Rubbish. Junk. Garbage. Disaster.",
        "rating": 1, "verified": False, "label": 1
    },
    {
        "text": "My cousin also bought this and he also said it is amazing product. Even my "
                "neighbour has this and he is also happy. Everyone I know who has this product "
                "loves it very much. Must buy for everyone.",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "DO NOT BUY THIS PRODUCT! I know for a fact that these are returned products "
                "being resold! All my friends received defective units! BEWARE!",
        "rating": 1, "verified": False, "label": 1
    },
    {
        "text": "Product received. Working fine. Thanks. Good packaging. Fast delivery.",
        "rating": 4, "verified": True, "label": 1
    },
    {
        "text": "Osm product bro.. bahut accha hai.. must buy.. bass le lo sab log..",
        "rating": 5, "verified": True, "label": 1
    },
    {
        "text": "Don't listen to negative reviews they are all competitor's reviews. This is genuinely "
                "the best product. Competitors are jealous. Buy with confidence.",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "Return this and buy [BRAND X] instead. Much better product. This company doesn't "
                "deserve your money. Trust me I have used both.",
        "rating": 1, "verified": False, "label": 1
    },
    {
        "text": "Awesome awesome awesome!!! Best investment of 2024!! Worth every single penny!! "
                "Mindblowing quality!! 🔥🔥🔥🔥🔥",
        "rating": 5, "verified": False, "label": 1
    },
    {
        "text": "Bakwas product. Faltu. Bekaar. Don't waste money. Seller is cheater.",
        "rating": 1, "verified": False, "label": 1
    },
]

# Summary statistics
if __name__ == "__main__":
    genuine = sum(1 for r in LABELED_REVIEWS if r["label"] == 0)
    fake = sum(1 for r in LABELED_REVIEWS if r["label"] == 1)
    print(f"Total samples: {len(LABELED_REVIEWS)}")
    print(f"  Genuine: {genuine}")
    print(f"  Fake:    {fake}")
    print(f"  Ratio:   {genuine/fake:.2f}:1")
