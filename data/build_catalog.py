"""Build data/products.json: a 200-product electronics catalog for a Kenyan shop.

The catalog deliberately contains near-duplicates (iPhone 16 / 16 Pro / 15 / 14,
cases for several phone models, many headphones) so the search has to work.
Prices are in Kenyan shillings (KES): converted from the US list price at
KES_PER_USD, which includes a rough import/retail markup, and rounded to
shop-style prices like 119,999.

    python data/build_catalog.py
"""
import json
import random
from pathlib import Path

KES_PER_USD = 150

# (id, name, brand, category, price_usd, description)
PRODUCTS = [
    # ---------------------------------------------------------------- phones (30)
    ("iphone-16-pro-max", "iPhone 16 Pro Max 256GB", "Apple", "phones", 1199, "Apple's largest flagship phone with a 6.9-inch display, 5x telephoto camera and the longest iPhone battery life."),
    ("iphone-16-pro", "iPhone 16 Pro 128GB", "Apple", "phones", 999, "Apple flagship phone with a titanium body, triple camera with 5x zoom and a camera control button, ideal for photography and video."),
    ("iphone-16", "iPhone 16 128GB", "Apple", "phones", 799, "Apple smartphone with a 6.1-inch display, 48MP dual camera, action button and USB-C charging."),
    ("iphone-16e", "iPhone 16e 128GB", "Apple", "phones", 599, "The most affordable current iPhone with a single 48MP camera, Face ID and all-day battery."),
    ("iphone-15-pro", "iPhone 15 Pro 128GB", "Apple", "phones", 899, "Previous Apple flagship with a titanium body, triple camera with 3x zoom and USB-C."),
    ("iphone-15", "iPhone 15 128GB", "Apple", "phones", 699, "Apple smartphone with a 6.1-inch display, Dynamic Island, dual camera and USB-C charging."),
    ("iphone-15-plus", "iPhone 15 Plus 128GB", "Apple", "phones", 799, "Apple smartphone with a large 6.7-inch display and very long battery life."),
    ("iphone-14", "iPhone 14 128GB", "Apple", "phones", 599, "Older-generation Apple smartphone with a 6.1-inch display, dual camera and Lightning port."),
    ("iphone-se-3", "iPhone SE (3rd generation) 64GB", "Apple", "phones", 429, "Compact budget iPhone with a 4.7-inch screen, home button with Touch ID and a single camera."),
    ("galaxy-s25-ultra", "Samsung Galaxy S25 Ultra 256GB", "Samsung", "phones", 1299, "Samsung's top Android phone with a built-in S Pen, 200MP camera with 100x space zoom and a titanium frame."),
    ("galaxy-s25", "Samsung Galaxy S25 128GB", "Samsung", "phones", 799, "Compact Samsung flagship with a 6.2-inch AMOLED screen, Galaxy AI features and a triple camera."),
    ("galaxy-s24", "Samsung Galaxy S24 128GB", "Samsung", "phones", 699, "Previous-generation Samsung flagship with a 6.2-inch AMOLED screen and AI photo editing."),
    ("galaxy-a55", "Samsung Galaxy A55 5G 128GB", "Samsung", "phones", 449, "Mid-range Samsung phone with a 120Hz AMOLED screen, IP67 water resistance and a big battery."),
    ("galaxy-a15", "Samsung Galaxy A15 128GB", "Samsung", "phones", 179, "Budget Samsung Android phone with a 6.5-inch screen and a 5000mAh battery that lasts two days."),
    ("galaxy-z-flip6", "Samsung Galaxy Z Flip6 256GB", "Samsung", "phones", 1099, "Foldable clamshell phone that folds in half to fit in a small pocket, with a cover screen for selfies."),
    ("galaxy-z-fold6", "Samsung Galaxy Z Fold6 256GB", "Samsung", "phones", 1899, "Foldable phone that opens into a 7.6-inch tablet for multitasking and reading."),
    ("pixel-9-pro", "Google Pixel 9 Pro 128GB", "Google", "phones", 999, "Google flagship phone with the best computational photography, 5x telephoto and Gemini AI built in."),
    ("pixel-9", "Google Pixel 9 128GB", "Google", "phones", 799, "Google Android phone with a clean software experience, excellent camera and 7 years of updates."),
    ("pixel-8a", "Google Pixel 8a 128GB", "Google", "phones", 499, "Affordable Google phone with a flagship-quality camera and 7 years of Android updates."),
    ("oneplus-13", "OnePlus 13 256GB", "OnePlus", "phones", 899, "Fast Android flagship with 100W charging that fills the battery in about 30 minutes and a Hasselblad camera."),
    ("oneplus-nord-4", "OnePlus Nord 4 256GB", "OnePlus", "phones", 449, "Mid-range Android phone with a metal unibody, very fast charging and a smooth 120Hz display."),
    ("xiaomi-14-ultra", "Xiaomi 14 Ultra 512GB", "Xiaomi", "phones", 1299, "Camera-focused flagship with a 1-inch Leica main sensor and four rear cameras for serious photographers."),
    ("redmi-note-13", "Xiaomi Redmi Note 13 128GB", "Xiaomi", "phones", 199, "Budget Android phone with a 108MP camera, AMOLED screen and 33W fast charging."),
    ("tecno-camon-30", "Tecno Camon 30 256GB", "Tecno", "phones", 249, "Affordable phone with a 50MP selfie camera, dual SIM and a large 5000mAh battery."),
    ("infinix-hot-40", "Infinix Hot 40 128GB", "Infinix", "phones", 149, "Entry-level dual-SIM Android phone with a big screen and a 5000mAh battery at a low price."),
    ("nokia-g42", "Nokia G42 5G 128GB", "Nokia", "phones", 199, "Durable budget 5G phone that you can repair yourself, with a replaceable battery and screen."),
    ("motorola-edge-50", "Motorola Edge 50 Pro 256GB", "Motorola", "phones", 549, "Curved-screen Android phone with 125W charging and a vegan leather back."),
    ("itel-a70", "itel A70 128GB", "itel", "phones", 79, "Very affordable dual-SIM Android phone with a 6.6-inch screen and a 5000mAh battery."),
    ("nothing-phone-2a", "Nothing Phone (2a) 128GB", "Nothing", "phones", 349, "Stylish mid-range phone with a transparent back, Glyph light notifications and clean Android software."),
    ("nokia-105", "Nokia 105 (2023)", "Nokia", "phones", 25, "Simple button phone for elderly parents with big keys, a torch, FM radio and a battery that lasts for days; works with M-Pesa."),
    # ------------------------------------------------------- headphones & audio (22)
    ("airpods-pro-2", "AirPods Pro 2", "Apple", "headphones", 249, "Wireless earbuds with active noise cancellation, transparency mode and a hearing aid feature."),
    ("airpods-4", "AirPods 4", "Apple", "headphones", 129, "Open-fit wireless earbuds for iPhone with spatial audio and a small USB-C charging case."),
    ("airpods-max", "AirPods Max", "Apple", "headphones", 549, "Premium over-ear Apple headphones with aluminium cups, noise cancellation and spatial audio."),
    ("sony-wh1000xm5", "Sony WH-1000XM5", "Sony", "headphones", 379, "Over-ear wireless headphones with industry-leading noise cancelling, great for flights and commuting."),
    ("sony-wf1000xm5", "Sony WF-1000XM5", "Sony", "headphones", 279, "Small wireless earbuds with excellent noise cancelling and high-resolution sound."),
    ("bose-qc-ultra-headphones", "Bose QuietComfort Ultra Headphones", "Bose", "headphones", 429, "Comfortable over-ear headphones with world-class noise cancellation for long trips."),
    ("bose-qc-ultra-earbuds", "Bose QuietComfort Ultra Earbuds", "Bose", "headphones", 299, "Wireless earbuds with top-tier noise cancellation and immersive audio."),
    ("galaxy-buds3-pro", "Samsung Galaxy Buds3 Pro", "Samsung", "headphones", 249, "Samsung wireless earbuds with noise cancellation and real-time interpreter for Galaxy phones."),
    ("pixel-buds-pro-2", "Google Pixel Buds Pro 2", "Google", "headphones", 229, "Small, light Google earbuds with noise cancellation and Gemini assistant."),
    ("beats-studio-pro", "Beats Studio Pro", "Beats", "headphones", 349, "Over-ear wireless headphones with bold bass, noise cancelling and USB-C lossless audio."),
    ("beats-fit-pro", "Beats Fit Pro", "Beats", "headphones", 199, "Sport earbuds with secure wingtips that stay in during workouts, with noise cancelling."),
    ("jbl-tune-520bt", "JBL Tune 520BT", "JBL", "headphones", 49, "Cheap on-ear Bluetooth headphones with 57 hours of battery and foldable design."),
    ("jbl-live-pro-2", "JBL Live Pro 2", "JBL", "headphones", 149, "True wireless earbuds with adaptive noise cancelling and 40 hours of total playtime."),
    ("sennheiser-momentum-4", "Sennheiser Momentum 4 Wireless", "Sennheiser", "headphones", 349, "Audiophile over-ear wireless headphones with 60-hour battery and detailed sound."),
    ("soundcore-q30", "Anker Soundcore Life Q30", "Anker", "headphones", 79, "Budget over-ear headphones with hybrid noise cancelling and 40 hours of playtime."),
    ("shokz-openrun-pro", "Shokz OpenRun Pro", "Shokz", "headphones", 179, "Bone conduction headphones for running that leave your ears open to hear traffic."),
    ("jabra-elite-8-active", "Jabra Elite 8 Active", "Jabra", "headphones", 199, "Rugged sport earbuds that are sweatproof, waterproof and dustproof for the gym."),
    ("sony-mdr-zx110", "Sony MDR-ZX110 Wired Headphones", "Sony", "headphones", 19, "Very cheap wired on-ear headphones with a 3.5mm jack."),
    ("apple-earpods-usbc", "Apple EarPods (USB-C)", "Apple", "headphones", 19, "Wired earphones with a USB-C connector and built-in remote and microphone."),
    ("arctis-nova-7", "SteelSeries Arctis Nova 7", "SteelSeries", "headphones", 179, "Wireless gaming headset with a retractable microphone for PC, PlayStation and Switch."),
    ("hyperx-cloud-iii", "HyperX Cloud III", "HyperX", "headphones", 99, "Comfortable wired gaming headset with a detachable noise-cancelling microphone."),
    ("marshall-major-iv", "Marshall Major IV", "Marshall", "headphones", 149, "Iconic on-ear Bluetooth headphones with 80+ hours of battery and wireless charging."),
    # ----------------------------------------------------------------- laptops (22)
    ("macbook-air-13-m3", "MacBook Air 13-inch M3", "Apple", "laptops", 1099, "Thin and light Apple laptop for students and office work with an 18-hour battery and silent fanless design."),
    ("macbook-air-15-m3", "MacBook Air 15-inch M3", "Apple", "laptops", 1299, "Large-screen thin Apple laptop with a 15.3-inch display and all-day battery life."),
    ("macbook-pro-14-m4", "MacBook Pro 14-inch M4", "Apple", "laptops", 1599, "Professional Apple laptop with a Liquid Retina XDR display for photo editing and programming."),
    ("macbook-pro-16-m4-max", "MacBook Pro 16-inch M4 Max", "Apple", "laptops", 3499, "Most powerful Apple laptop for video editing, 3D rendering and machine learning work."),
    ("dell-xps-13", "Dell XPS 13", "Dell", "laptops", 1199, "Premium compact Windows ultrabook with an edge-to-edge display and aluminium build."),
    ("dell-inspiron-15", "Dell Inspiron 15", "Dell", "laptops", 549, "Affordable everyday Windows laptop for browsing, school work and video calls."),
    ("hp-pavilion-15", "HP Pavilion 15", "HP", "laptops", 649, "Mainstream Windows laptop with a full-size keyboard and numeric keypad for home and office."),
    ("hp-envy-x360", "HP Envy x360 14", "HP", "laptops", 899, "2-in-1 convertible Windows laptop with a touchscreen that folds into a tablet and supports a pen."),
    ("thinkpad-x1-carbon", "Lenovo ThinkPad X1 Carbon Gen 12", "Lenovo", "laptops", 1799, "Business laptop with a legendary keyboard, very light carbon fibre body and strong security features."),
    ("ideapad-slim-3", "Lenovo IdeaPad Slim 3", "Lenovo", "laptops", 449, "Budget slim Windows laptop for students with a 15.6-inch screen."),
    ("legion-5", "Lenovo Legion 5 Gaming Laptop", "Lenovo", "laptops", 1299, "Gaming laptop with an RTX 4060 graphics card and a 165Hz display for modern games."),
    ("rog-zephyrus-g14", "ASUS ROG Zephyrus G14", "ASUS", "laptops", 1599, "Compact 14-inch gaming laptop with an RTX graphics card and an OLED display."),
    ("zenbook-14-oled", "ASUS Zenbook 14 OLED", "ASUS", "laptops", 999, "Light Windows laptop with a vivid OLED screen and long battery life for travel."),
    ("vivobook-15", "ASUS Vivobook 15", "ASUS", "laptops", 399, "Cheap everyday Windows laptop for web browsing, email and streaming."),
    ("acer-aspire-5", "Acer Aspire 5", "Acer", "laptops", 499, "Value Windows laptop with a 15.6-inch Full HD screen and a backlit keyboard."),
    ("acer-chromebook-314", "Acer Chromebook 314", "Acer", "laptops", 279, "Simple ChromeOS laptop for kids and school, fast to start with long battery life."),
    ("acer-nitro-v-15", "Acer Nitro V 15", "Acer", "laptops", 799, "Entry-level gaming laptop with an RTX 4050 graphics card at a budget price."),
    ("msi-katana-15", "MSI Katana 15", "MSI", "laptops", 999, "Gaming laptop with an RTX 4070 graphics card and a 144Hz screen."),
    ("surface-laptop-7", "Microsoft Surface Laptop 7", "Microsoft", "laptops", 999, "Copilot+ Windows laptop with a Snapdragon chip, touchscreen and excellent battery life."),
    ("surface-pro-11", "Microsoft Surface Pro 11", "Microsoft", "laptops", 999, "Windows tablet that becomes a laptop with a detachable keyboard, great for note taking with a pen."),
    ("framework-laptop-13", "Framework Laptop 13", "Framework", "laptops", 1049, "Modular laptop you can repair and upgrade yourself, with swappable ports."),
    ("razer-blade-16", "Razer Blade 16", "Razer", "laptops", 2999, "High-end gaming laptop with an RTX 4090 graphics card and a dual-mode mini-LED display."),
    # ----------------------------------------------------------------- tablets (14)
    ("ipad-10", "iPad (10th generation) 64GB", "Apple", "tablets", 349, "Affordable Apple tablet with a 10.9-inch display, good for kids, streaming and schoolwork."),
    ("ipad-air-m2", "iPad Air 11-inch M2", "Apple", "tablets", 599, "Thin and powerful Apple tablet that supports Apple Pencil Pro for drawing and note taking."),
    ("ipad-pro-m4", "iPad Pro 13-inch M4", "Apple", "tablets", 1299, "Apple's most powerful tablet with an Ultra Retina OLED display for professional artists."),
    ("ipad-mini-7", "iPad mini (7th generation)", "Apple", "tablets", 499, "Small 8.3-inch Apple tablet that fits in one hand, great for reading and travel."),
    ("galaxy-tab-s9-fe", "Samsung Galaxy Tab S9 FE", "Samsung", "tablets", 449, "Mid-range Android tablet with an included S Pen and water resistance."),
    ("galaxy-tab-s10-ultra", "Samsung Galaxy Tab S10 Ultra", "Samsung", "tablets", 1199, "Huge 14.6-inch AMOLED Android tablet for productivity and movies."),
    ("galaxy-tab-a9", "Samsung Galaxy Tab A9+", "Samsung", "tablets", 219, "Budget 11-inch Android tablet for watching videos and browsing."),
    ("lenovo-tab-m11", "Lenovo Tab M11", "Lenovo", "tablets", 199, "Affordable family Android tablet with a pen included and a kids mode."),
    ("fire-hd-10", "Amazon Fire HD 10", "Amazon", "tablets", 139, "Cheap 10-inch tablet for streaming movies, reading and Alexa."),
    ("fire-hd-8-kids", "Amazon Fire HD 8 Kids", "Amazon", "tablets", 149, "Kids tablet with a drop-proof case, parental controls and a 2-year worry-free guarantee."),
    ("kindle-paperwhite", "Kindle Paperwhite", "Amazon", "tablets", 159, "Waterproof e-reader with a glare-free screen for reading books in sunlight and weeks of battery."),
    ("kindle-scribe", "Kindle Scribe", "Amazon", "tablets", 399, "Large e-reader you can also write on with a pen, for reading and handwritten notes."),
    ("sun-king-home-60", "Sun King Home 60 Solar Kit", "Sun King", "power", 129, "Solar home system with a panel, three lights, a radio and phone charging for homes off the grid or during blackouts."),
    ("xiaomi-pad-6", "Xiaomi Pad 6", "Xiaomi", "tablets", 349, "Android tablet with a 144Hz display and quad speakers at a mid-range price."),
    # ---------------------------------------------------------- wearables (14)
    ("apple-watch-series-10", "Apple Watch Series 10", "Apple", "wearables", 399, "Smartwatch that tracks fitness, heart rate and sleep, and shows iPhone notifications."),
    ("apple-watch-ultra-2", "Apple Watch Ultra 2", "Apple", "wearables", 799, "Rugged titanium smartwatch for diving, hiking and endurance sports with precise GPS."),
    ("apple-watch-se", "Apple Watch SE", "Apple", "wearables", 249, "Affordable Apple smartwatch with fall detection, crash detection and fitness tracking."),
    ("galaxy-watch-7", "Samsung Galaxy Watch7", "Samsung", "wearables", 299, "Android smartwatch with health tracking, sleep coaching and Samsung phone integration."),
    ("galaxy-watch-ultra", "Samsung Galaxy Watch Ultra", "Samsung", "wearables", 649, "Rugged Android smartwatch with long battery life for outdoor adventures."),
    ("pixel-watch-3", "Google Pixel Watch 3", "Google", "wearables", 349, "Round Android smartwatch with Fitbit health tracking and loss of pulse detection."),
    ("garmin-forerunner-265", "Garmin Forerunner 265", "Garmin", "wearables", 449, "GPS running watch with training readiness, race predictions and an AMOLED screen."),
    ("garmin-fenix-8", "Garmin Fenix 8", "Garmin", "wearables", 999, "Premium multisport GPS watch with maps, a flashlight and weeks of battery for adventurers."),
    ("garmin-venu-3", "Garmin Venu 3", "Garmin", "wearables", 449, "Health and fitness smartwatch with sleep coaching and a bright AMOLED display."),
    ("fitbit-charge-6", "Fitbit Charge 6", "Fitbit", "wearables", 159, "Fitness tracker band with heart rate, built-in GPS and a week of battery."),
    ("fitbit-inspire-3", "Fitbit Inspire 3", "Fitbit", "wearables", 99, "Simple, cheap fitness tracker that counts steps and tracks sleep."),
    ("xiaomi-smart-band-9", "Xiaomi Smart Band 9", "Xiaomi", "wearables", 49, "Very affordable fitness band with step counting, sleep tracking and two weeks of battery."),
    ("amazfit-gtr-4", "Amazfit GTR 4", "Amazfit", "wearables", 199, "Classic-looking smartwatch with GPS, health monitoring and two weeks of battery."),
    ("huawei-watch-gt-4", "Huawei Watch GT 4", "Huawei", "wearables", 249, "Elegant smartwatch with fitness tracking and up to 14 days of battery life."),
    # ----------------------------------------------------------------- cameras (12)
    ("sony-a7-iv", "Sony Alpha 7 IV", "Sony", "cameras", 2499, "Full-frame mirrorless camera for professional photography and 4K video."),
    ("sony-zv-e10", "Sony ZV-E10 II", "Sony", "cameras", 999, "Interchangeable-lens vlogging camera with a flip screen and great autofocus for YouTubers."),
    ("canon-eos-r50", "Canon EOS R50", "Canon", "cameras", 679, "Beginner-friendly mirrorless camera with a kit lens, easy guided menus and 4K video."),
    ("canon-eos-r6-ii", "Canon EOS R6 Mark II", "Canon", "cameras", 2499, "Fast full-frame mirrorless camera for sports and wildlife photography."),
    ("nikon-z50", "Nikon Z50 II", "Nikon", "cameras", 859, "Compact APS-C mirrorless camera for travel and family photos."),
    ("fujifilm-x100vi", "Fujifilm X100VI", "Fujifilm", "cameras", 1599, "Premium compact camera with a fixed lens and film simulations for street photography."),
    ("instax-mini-12", "Fujifilm Instax Mini 12", "Fujifilm", "cameras", 79, "Instant camera that prints credit-card-sized photos immediately, fun for parties."),
    ("gopro-hero-13", "GoPro HERO13 Black", "GoPro", "cameras", 399, "Waterproof action camera for surfing, biking and skiing with 5.3K video and stabilisation."),
    ("dji-osmo-pocket-3", "DJI Osmo Pocket 3", "DJI", "cameras", 519, "Pocket gimbal camera with a 1-inch sensor for smooth handheld vlogging."),
    ("dji-mini-4-pro", "DJI Mini 4 Pro", "DJI", "cameras", 759, "Small camera drone under 249g that records 4K aerial video with obstacle avoidance."),
    ("insta360-x4", "Insta360 X4", "Insta360", "cameras", 499, "360-degree action camera that captures everything around you in 8K."),
    ("logitech-c920", "Logitech C920 HD Pro Webcam", "Logitech", "cameras", 69, "Full HD 1080p webcam for video calls, Zoom meetings and streaming."),
    # ------------------------------------------------------- cases & accessories (20)
    ("case-iphone-16-pro-silicone", "iPhone 16 Pro Silicone Case with MagSafe", "Apple", "accessories", 49, "Soft-touch silicone cover for the iPhone 16 Pro with MagSafe magnets."),
    ("case-iphone-16-clear", "iPhone 16 Clear Case with MagSafe", "Apple", "accessories", 49, "Transparent protective case for the iPhone 16 that shows off the phone colour."),
    ("case-iphone-15-silicone", "iPhone 15 Silicone Case", "Apple", "accessories", 49, "Soft protective cover for the iPhone 15, available in several colours."),
    ("case-iphone-15-pro-leather", "iPhone 15 Pro FineWoven Case", "Apple", "accessories", 59, "Premium woven fabric case for the iPhone 15 Pro with MagSafe."),
    ("case-iphone-14-clear", "iPhone 14 Clear Case", "Spigen", "accessories", 15, "Slim clear bumper case for the iPhone 14 with raised edges to protect the camera."),
    ("case-galaxy-s25-ultra-rugged", "Galaxy S25 Ultra Rugged Case", "Samsung", "accessories", 39, "Heavy-duty drop protection case for the Galaxy S25 Ultra with a kickstand."),
    ("case-galaxy-s24-clear", "Galaxy S24 Clear Case", "Samsung", "accessories", 19, "Thin transparent case for the Samsung Galaxy S24."),
    ("case-pixel-9-pro", "Pixel 9 Pro Case", "Google", "accessories", 29, "Recycled-material protective case for the Google Pixel 9 Pro."),
    ("otterbox-defender-iphone-16", "OtterBox Defender for iPhone 16", "OtterBox", "accessories", 59, "Military-grade rugged case for the iPhone 16 for construction sites and outdoor work."),
    ("spigen-tough-armor-s25", "Spigen Tough Armor for Galaxy S25", "Spigen", "accessories", 25, "Dual-layer shockproof case for the Galaxy S25 with a built-in kickstand."),
    ("wallet-case-iphone-15", "iPhone 15 Leather Wallet Case", "Bellroy", "accessories", 69, "Leather case for the iPhone 15 that holds three cards and cash, so you can leave your wallet at home."),
    ("screen-protector-iphone-16", "iPhone 16 Tempered Glass Screen Protector (2-pack)", "ZAGG", "accessories", 29, "Tempered glass screen protector that prevents scratches and cracks on the iPhone 16 display."),
    ("screen-protector-galaxy-s24", "Galaxy S24 Screen Protector", "Spigen", "accessories", 19, "Tempered glass protector for the Samsung Galaxy S24 screen with easy installation."),
    ("ipad-air-smart-folio", "Smart Folio for iPad Air", "Apple", "accessories", 79, "Thin magnetic cover for the iPad Air that folds into a stand and wakes the screen."),
    ("ipad-keyboard-case", "Logitech Combo Touch for iPad (10th gen)", "Logitech", "accessories", 159, "Keyboard case with a trackpad that turns the iPad into a laptop for typing."),
    ("macbook-sleeve", "13-inch Laptop Sleeve", "Incase", "accessories", 39, "Padded sleeve that protects a 13-inch MacBook or laptop inside your bag."),
    ("laptop-backpack", "Anti-Theft Laptop Backpack 15.6-inch", "Targus", "accessories", 69, "Water-resistant backpack with a padded laptop compartment, hidden zips and a USB charging port."),
    ("waterproof-phone-pouch", "Waterproof Phone Pouch", "JOTO", "accessories", 12, "Sealed waterproof bag that keeps your phone dry at the beach, pool or on a boat."),
    ("popsocket", "PopSockets PopGrip", "PopSockets", "accessories", 15, "Expanding grip and stand that sticks to the back of your phone for one-handed use."),
    ("car-phone-mount", "Magnetic Car Phone Mount", "iOttie", "accessories", 35, "Dashboard or air vent mount that holds your phone for navigation while driving."),
    # ------------------------------------------------------- power & cables (20)
    ("apple-20w-usbc", "Apple 20W USB-C Power Adapter", "Apple", "power", 19, "Official Apple wall charger for fast charging iPhone and iPad."),
    ("samsung-25w-charger", "Samsung 25W Super Fast Charger", "Samsung", "power", 19, "USB-C wall charger for super fast charging Samsung Galaxy phones."),
    ("anker-nano-30w", "Anker Nano 30W USB-C Charger", "Anker", "power", 22, "Tiny GaN wall charger that fast charges phones and small tablets."),
    ("anker-65w-gan", "Anker 65W GaN Charger (3 ports)", "Anker", "power", 49, "Compact charger that powers a laptop, phone and earbuds at the same time."),
    ("ugreen-100w", "UGREEN Nexode 100W 4-Port Charger", "UGREEN", "power", 69, "Desktop charging station with four ports that can charge a MacBook Pro and phones together."),
    ("magsafe-charger", "Apple MagSafe Charger", "Apple", "power", 39, "Magnetic wireless charging puck that snaps onto the back of an iPhone."),
    ("belkin-3in1-magsafe", "Belkin BoostCharge Pro 3-in-1 MagSafe Stand", "Belkin", "power", 129, "Bedside charging stand for iPhone, Apple Watch and AirPods at the same time."),
    ("anker-powercore-10000", "Anker PowerCore 10000", "Anker", "power", 25, "Pocket-sized power bank that recharges a phone about twice when you are away from a socket."),
    ("anker-737-powerbank", "Anker 737 Power Bank 24000mAh", "Anker", "power", 109, "High-capacity 140W power bank that can recharge a laptop on the go."),
    ("xiaomi-20000-powerbank", "Xiaomi 20000mAh Power Bank", "Xiaomi", "power", 35, "Large-capacity portable battery for charging phones several times on long trips."),
    ("usbc-lightning-cable", "USB-C to Lightning Cable 1m", "Apple", "power", 19, "Charging and sync cable for older iPhones with a Lightning port."),
    ("usbc-cable-240w", "USB-C to USB-C Cable 2m 240W", "Anker", "power", 15, "Long braided USB-C cable for fast charging laptops, phones and tablets."),
    ("usba-usbc-cable", "USB-A to USB-C Cable 1m", "UGREEN", "power", 9, "Cable for charging USB-C phones from an older USB-A charger or computer port."),
    ("car-charger-usbc", "Dual USB-C Car Charger 40W", "Anker", "power", 25, "Car cigarette lighter charger that fast charges two phones while driving."),
    ("wireless-charging-pad", "15W Wireless Charging Pad", "Belkin", "power", 29, "Flat Qi wireless charger: just place any compatible phone on it to charge."),
    ("apple-watch-charger", "Apple Watch Magnetic Fast Charger (USB-C)", "Apple", "power", 29, "Replacement magnetic charging cable for the Apple Watch."),
    ("travel-adapter", "Universal Travel Adapter with USB-C", "EPICKA", "power", 29, "All-in-one plug adapter for travelling to the UK, Europe, US and Australia with USB ports."),
    ("usbc-hub-7in1", "USB-C Hub 7-in-1", "Anker", "power", 39, "Adds HDMI, USB-A ports and an SD card reader to a laptop that only has USB-C."),
    ("solar-powerbank", "Solar Power Bank 26800mAh", "BLAVOR", "power", 39, "Rugged power bank with a solar panel and flashlight for camping and power cuts."),
    ("ups-router-mini", "Mini UPS for Wi-Fi Router", "TP-Link", "power", 45, "Small battery backup that keeps your router and internet running during a blackout."),
    # --------------------------------------------------- smart home & speakers (16)
    ("echo-dot-5", "Amazon Echo Dot (5th gen)", "Amazon", "smart-home", 49, "Small smart speaker with Alexa for music, timers and controlling smart home devices by voice."),
    ("echo-show-8", "Amazon Echo Show 8", "Amazon", "smart-home", 149, "Smart display with Alexa for video calls, recipes and viewing security cameras."),
    ("nest-mini", "Google Nest Mini", "Google", "smart-home", 49, "Compact smart speaker with Google Assistant for questions, music and smart home control."),
    ("nest-hub-2", "Google Nest Hub (2nd gen)", "Google", "smart-home", 99, "Smart display with Google Assistant that also tracks your sleep from the bedside."),
    ("homepod-mini", "Apple HomePod mini", "Apple", "smart-home", 99, "Small Siri smart speaker with rich sound that works with iPhone and Apple Music."),
    ("sonos-era-100", "Sonos Era 100", "Sonos", "smart-home", 249, "Premium Wi-Fi speaker for room-filling stereo sound that can be part of a multi-room system."),
    ("jbl-flip-6", "JBL Flip 6", "JBL", "smart-home", 129, "Portable waterproof Bluetooth speaker for the beach, pool parties and outdoors."),
    ("jbl-charge-5", "JBL Charge 5", "JBL", "smart-home", 179, "Loud portable Bluetooth speaker with 20 hours of battery that can also charge your phone."),
    ("ue-wonderboom-4", "Ultimate Ears Wonderboom 4", "Ultimate Ears", "smart-home", 99, "Small rugged speaker that floats in water and survives drops."),
    ("marshall-emberton-iii", "Marshall Emberton III", "Marshall", "smart-home", 169, "Compact portable speaker with vintage style and 32+ hours of playtime."),
    ("ring-video-doorbell", "Ring Video Doorbell", "Ring", "smart-home", 99, "Doorbell with a camera so you can see and talk to visitors from your phone."),
    ("tapo-c200", "TP-Link Tapo C200 Security Camera", "TP-Link", "smart-home", 29, "Cheap indoor Wi-Fi camera with pan and tilt, night vision and motion alerts to watch your home or baby."),
    ("philips-hue-starter", "Philips Hue White and Colour Starter Kit", "Philips", "smart-home", 199, "Smart light bulbs you can dim and change colour from your phone or voice assistant."),
    ("deco-mesh-wifi", "TP-Link Deco X50 Mesh Wi-Fi (3-pack)", "TP-Link", "smart-home", 249, "Mesh Wi-Fi system that removes dead zones and gives strong internet in every room of a large house."),
    ("huawei-4g-mifi", "Huawei E5576 4G MiFi", "Huawei", "smart-home", 49, "Pocket Wi-Fi hotspot: insert a Safaricom or Airtel SIM card to share mobile data with up to 16 devices."),
    ("chromecast-google-tv", "Google TV Streamer", "Google", "smart-home", 99, "Plugs into your TV to stream Netflix, YouTube and live TV in 4K."),
    # ------------------------------------------------------------------ gaming (14)
    ("ps5-slim", "PlayStation 5 Slim (Disc Edition)", "Sony", "gaming", 499, "Sony home game console with a disc drive for exclusive games like Spider-Man."),
    ("ps5-pro", "PlayStation 5 Pro", "Sony", "gaming", 699, "The most powerful PlayStation with enhanced graphics for 4K gaming."),
    ("dualsense", "DualSense Wireless Controller", "Sony", "gaming", 74, "PS5 controller with haptic feedback and adaptive triggers."),
    ("xbox-series-x", "Xbox Series X", "Microsoft", "gaming", 499, "Microsoft's most powerful console for 4K gaming and Game Pass."),
    ("xbox-series-s", "Xbox Series S", "Microsoft", "gaming", 299, "Small all-digital Xbox console that is the cheapest way to play Game Pass games."),
    ("xbox-controller", "Xbox Wireless Controller", "Microsoft", "gaming", 59, "Wireless controller for Xbox consoles and Windows PCs."),
    ("switch-oled", "Nintendo Switch OLED", "Nintendo", "gaming", 349, "Handheld and TV game console with a vivid OLED screen, perfect for Mario and family games."),
    ("switch-2", "Nintendo Switch 2", "Nintendo", "gaming", 449, "Nintendo's newest hybrid console with a bigger screen and magnetic Joy-Con controllers."),
    ("switch-pro-controller", "Nintendo Switch Pro Controller", "Nintendo", "gaming", 69, "Traditional wireless controller for comfortable long sessions on the Nintendo Switch."),
    ("steam-deck-oled", "Steam Deck OLED 512GB", "Valve", "gaming", 549, "Handheld gaming PC that plays your Steam library of PC games anywhere."),
    ("meta-quest-3", "Meta Quest 3 512GB", "Meta", "gaming", 499, "Virtual and mixed reality headset for immersive games and fitness, no PC needed."),
    ("meta-quest-3s", "Meta Quest 3S 128GB", "Meta", "gaming", 299, "Affordable standalone VR headset for getting started with virtual reality."),
    ("razer-kishi-v2", "Razer Kishi V2", "Razer", "gaming", 99, "Controller that clips onto your phone to turn it into a handheld game console."),
    ("ea-fc-25-ps5", "EA Sports FC 25 (PS5)", "EA", "gaming", 69, "Football video game for PlayStation 5 with real clubs and players."),
    # ------------------------------------------- computer peripherals & storage (16)
    ("mx-master-3s", "Logitech MX Master 3S", "Logitech", "computer", 99, "Ergonomic wireless mouse for productivity with quiet clicks and a fast scroll wheel."),
    ("g-pro-superlight-2", "Logitech G Pro X Superlight 2", "Logitech", "computer", 159, "Ultra-light wireless gaming mouse used by esports professionals."),
    ("logitech-m185", "Logitech M185 Wireless Mouse", "Logitech", "computer", 15, "Cheap compact wireless mouse with a USB receiver for laptops."),
    ("magic-keyboard", "Apple Magic Keyboard", "Apple", "computer", 99, "Slim wireless rechargeable keyboard for Mac and iPad."),
    ("mx-keys-s", "Logitech MX Keys S", "Logitech", "computer", 109, "Comfortable backlit wireless keyboard that switches between three computers."),
    ("keychron-k2", "Keychron K2 Mechanical Keyboard", "Keychron", "computer", 89, "Compact wireless mechanical keyboard for Mac and Windows with tactile switches for typing and coding."),
    ("razer-blackwidow-v4", "Razer BlackWidow V4", "Razer", "computer", 169, "RGB mechanical gaming keyboard with macro keys and a wrist rest."),
    ("dell-ultrasharp-27-4k", "Dell UltraSharp 27 4K USB-C Monitor", "Dell", "computer", 579, "27-inch 4K monitor with accurate colours and USB-C that charges your laptop with one cable."),
    ("lg-ultragear-27", "LG UltraGear 27-inch 165Hz Gaming Monitor", "LG", "computer", 249, "Fast 165Hz QHD gaming monitor with 1ms response time."),
    ("samsung-odyssey-g9", "Samsung Odyssey OLED G9 49-inch", "Samsung", "computer", 1299, "Super-ultrawide curved 49-inch OLED gaming monitor."),
    ("samsung-t7-1tb", "Samsung T7 Portable SSD 1TB", "Samsung", "computer", 99, "Pocket-sized fast external SSD for backing up photos and transferring large files."),
    ("sandisk-extreme-2tb", "SanDisk Extreme Portable SSD 2TB", "SanDisk", "computer", 169, "Rugged water-resistant external SSD for photographers and video editors on the go."),
    ("wd-elements-4tb", "WD Elements 4TB External Hard Drive", "Western Digital", "computer", 99, "Large cheap external hard drive for backups and storing movies."),
    ("sandisk-usb-128gb", "SanDisk Ultra 128GB USB Flash Drive", "SanDisk", "computer", 12, "Small USB stick for carrying documents and files between computers."),
    ("samsung-evo-microsd-256", "Samsung EVO Plus 256GB microSD Card", "Samsung", "computer", 25, "Memory card to add storage to phones, Nintendo Switch, drones and action cameras."),
    ("epson-ecotank", "Epson EcoTank ET-2850 Printer", "Epson", "computer", 279, "Home printer with refillable ink tanks that is very cheap to run, also scans and copies."),
]


def to_kes(price_usd):
    """US price -> shop-style KES price, e.g. 799 USD -> 119,999 KES."""
    return max(499, round(price_usd * KES_PER_USD / 500) * 500 - 1)


def build():
    rng = random.Random(42)  # fixed seed: same stock numbers every time
    products = []
    for pid, name, brand, category, price_usd, description in PRODUCTS:
        stock = 0 if rng.random() < 0.1 else rng.randint(1, 40)
        products.append({"id": pid, "name": name, "brand": brand, "category": category,
                         "price": to_kes(price_usd), "currency": "KES", "stock": stock,
                         "description": description})
    ids = [p["id"] for p in products]
    assert len(ids) == len(set(ids)), "duplicate product ids"
    return products


if __name__ == "__main__":
    products = build()
    out = Path(__file__).resolve().parent / "products.json"
    out.write_text(json.dumps(products, indent=2) + "\n")
    print(f"wrote {len(products)} products to {out}")
