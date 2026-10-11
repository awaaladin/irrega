"""Words for the landing page. Written for a farmer: short sentences, no jargon without an explanation.
Static, authored text (rendered with |safe), never user input."""

TOC = [
    ("how", "How it works"), ("decisions", "The four decisions"), ("screens", "Every screen"),
    ("s-account", "Sign in and sign up"), ("s-setup", "Add your farm and fields"), ("s-today", "Today"),
    ("s-why", "Why this?"), ("s-override", "Override and snooze"), ("s-field", "Field detail"),
    ("s-ask", "Ask a question"), ("s-insights", "Insights"), ("s-alerts", "Alerts"),
    ("s-plans", "Plans and billing"), ("s-pilot", "Pilot results"), ("s-account-page", "Account and display"),
    ("s-partner", "Partner and system"), ("s-demo", "Demo controls"), ("words", "Words you will meet"), ("honest", "What we are honest about"),
]

SCREENS = [
    {
        "id": "s-account", "icon": "user", "where": "Sign in and Create account",
        "title": "Getting in",
        "purpose": "Your account keeps your farms, readings and decisions private to you. Nobody else can see your fields.",
        "sees": [
            "Sign in with your <strong>email or phone number</strong> and a password.",
            "Creating an account asks for your name, an email or phone, a password (8 characters or more) and, if you have one, a <strong>pilot code</strong>.",
            "A button to <strong>explore the sample farm</strong> without signing up.",
        ],
        "does": [
            "Start a free pilot trial. A pilot code from a cooperative or partner gives you a longer trial.",
            "Switch between the dark and light look with the sun and moon switch.",
            "Sign out any time from the Account screen.",
        ],
        "tip": "Too many wrong tries in a minute pauses sign-in briefly. That protects your account.",
    },
    {
        "id": "s-setup", "icon": "map-pin", "where": "Fields &rarr; Add a farm, then Add a field",
        "title": "Add your farm and fields",
        "purpose": "Two short forms. The first says where your farm is so we can fetch your weather. The second describes one field so the advice fits your crop and soil.",
        "sees": [
            "A <strong>satellite map</strong> of your area. Tap it or drag the pin to your farm. You can also type latitude and longitude, or press <em>Use my location</em>.",
            "For each field: its name, the <strong>crop</strong> (cassava, yam, maize, rice, plantain, tomato, pepper, okra, cucumber, waterleaf, cocoa seedlings), size in hectares, <strong>soil type</strong> (sandy, loam, clay, laterite), <strong>planting date</strong>, and <strong>how you water</strong> (drip, sprinkler, watering can or hose, flood).",
            "Size hint: a 50 x 100 ft plot is about 0.046 hectares.",
        ],
        "does": [
            "Add as many farms and fields as your plan allows.",
            "Edit a field later if something changes. Advice updates straight away.",
            "Remove a field you no longer grow.",
        ],
        "tip": "You do not choose the growth stage. We work it out from the crop and the planting date, and show how many days remain until the next stage.",
    },
    {
        "id": "s-today", "icon": "today", "where": "Today (the first screen after you sign in)",
        "title": "Today: one decision for each field",
        "purpose": "This is the screen to open each morning. It answers one question for every field, in about two seconds: should I water?",
        "sees": [
            "A <strong>card per field</strong> with the decision in large words, the crop and growth stage, and a note on when the advice was made.",
            "<strong>Depth and volume</strong>: how deep to water in millimetres, and what that is in litres, watering cans (15 litres each) or 200-litre drums.",
            "<strong>Best time</strong>: a window that avoids midday heat and forecast rain.",
            "<strong>Confidence</strong>: three bars and a word (High, Medium, Low). Low means something is missing or old, and the card says what.",
            "A line showing today's soil moisture against the <em>water-now line</em>.",
            "Below the cards: the <strong>5-day weather strip</strong> (rain chance shown as a filling circle, with the number), an estimate of <strong>water saved</strong>, and a <strong>crop-stress</strong> trend for each field.",
            "A <strong>set-up checklist</strong> until you have done the basics, and a <strong>suggestion</strong> when we notice a pattern, such as you often overriding skips.",
        ],
        "does": [
            "<strong>Accept advice</strong>, <strong>Override</strong> or <strong>Snooze</strong> right on the card.",
            "Open <strong>Why this?</strong> to see the reasons.",
            "Press <em>Send me the morning plan</em> to put today's summary in your alerts (and SMS or WhatsApp if you turned those on).",
            "Rate how the advice is working and leave a note for the pilot team.",
        ],
        "tip": "Once you accept or override a card, that day's advice is frozen so your history stays true to what you were shown.",
    },
    {
        "id": "s-why", "icon": "info", "where": "Why this? (opens under any decision)",
        "title": "Why this? The reasons, in plain words",
        "purpose": "So you never have to trust a number blindly. This panel shows exactly what the advice is based on, and what happens if you do something else.",
        "sees": [
            "A <strong>headline</strong> in one or two sentences, then <strong>numbered reasons</strong> ranked by importance. Example: <em>Rain is likely tomorrow afternoon and the soil still holds enough water, so we suggest skipping today.</em>",
            "<strong>If you wait 24 hours</strong>: whether the crop will be stressed, and how much water you would need tomorrow.",
            "<strong>What the advice is based on</strong>: bars for soil moisture, rain forecast, crop water use, growth stage, crop stress from satellite and last season's yield. Each bar shows its share of the decision and whether it pushes toward watering or skipping.",
            "If confidence is lower, a box explaining <strong>why</strong>.",
            "<em>Show the water numbers</em> reveals the full calculation for people who want to check it.",
        ],
        "does": [
            "Switch the explanation between <strong>English and Nigerian Pidgin</strong> with the EN / Pidgin switch at the top.",
            "Jump to <em>Ask a question about this</em> if something is unclear.",
        ],
        "tip": "A single watering is capped at 30 mm because more than that at once mostly runs off. When the soil could take more, we tell you to split it and check again tomorrow.",
    },
    {
        "id": "s-override", "icon": "pencil", "where": "Override and Snooze (buttons on every decision)",
        "title": "Override and snooze: you stay in control",
        "purpose": "You know your land better than any model. This is how you tell us what you actually did, so the record is honest and the advice can improve.",
        "sees": [
            "<strong>Override</strong> opens a sheet that rises from the button. On a phone you can drag it down to close.",
            "Three choices: <em>Water this field</em> (with a litres stepper and the cans equivalent), <em>Skip today</em>, or <em>Water at a different time</em>.",
            "Quick <strong>reason chips</strong> (Already watered, Rain started, No water available, I know my soil, Crop looks thirsty) and an optional note.",
        ],
        "does": [
            "Save your own choice. It is added to your <strong>decision history</strong>, which cannot be edited afterwards.",
            "<strong>Snooze</strong> to be reminded in a few hours instead of deciding now.",
            "Accept the advice with one tap when you agree.",
        ],
        "tip": "If you often override the same kind of advice on a field, we <em>suggest</em> being more cautious there. It only changes if you say yes.",
    },
    {
        "id": "s-field", "icon": "sprout", "where": "Fields &rarr; open a field",
        "title": "Field detail: everything about one field",
        "purpose": "The full picture for a single field, and the place to give it fresh information.",
        "sees": [
            "The same decision card, with a <strong>sticky action bar</strong> on phones so Accept is always within reach.",
            "<strong>Soil moisture slider</strong>: a thumb with weight that gently snaps to the water-now line, field capacity and the waterlogged level. Coloured bands show too dry, good range and waterlogged.",
            "<strong>Moisture trend</strong>: a chart of the last 30 days with the water-now line. A table version is one tap away for screen readers.",
            "<strong>Growth stage</strong>: the four stages with their length, and how many days until the next.",
            "<strong>Crop stress from satellite</strong> (NDVI): a small trend line, marked <em>simulated</em> when it is.",
            "The <strong>weather strip</strong>, the <strong>Ask</strong> panel, <strong>what you decided</strong> before, and <strong>harvests</strong>.",
        ],
        "does": [
            "Set a <strong>soil moisture reading</strong> and save it. Advice updates immediately.",
            "<strong>Import readings</strong> from a CSV file (two columns: date, moisture).",
            "Record last season's <strong>harvest</strong>, and tick the box if a dry spell hurt it. We then set the watering trigger a little earlier.",
            "Edit or remove the field.",
        ],
        "tip": "How to take a reading: push a probe or your finger about 10 cm into the soil. A fresh reading every day or two makes the advice noticeably stronger.",
    },
    {
        "id": "s-ask", "icon": "message", "where": "Ask panel (on each field)",
        "title": "Ask a question",
        "purpose": "Type a question in your own words. The assistant answers using only this field's soil reading, forecast and crop stage, and tells you plainly when it does not know.",
        "sees": [
            "A chat with <strong>suggested questions</strong>: <em>Why this?</em>, <em>What if I wait a day?</em>, <em>How much water if I only have 5 cans?</em>, <em>Is my crop stressed?</em>",
            "Answers that appear word by word as they are written.",
            "A badge reminding you answers are <strong>grounded in your data</strong>.",
        ],
        "does": [
            "Ask follow-up questions. The last few messages are remembered for that field.",
            "Use it offline? Questions need a connection, and the panel says so.",
        ],
        "tip": "Ask something it cannot know, such as a market price, and it will say it does not have that, instead of guessing.",
    },
    {
        "id": "s-insights", "icon": "chart", "where": "Insights tab",
        "title": "Insights: how your fields and the advice are doing",
        "purpose": "A step back from today. See trends across all fields and how much the advice has helped.",
        "sees": [
            "Three numbers: <strong>water saved</strong> over 30 days (an estimate, with its assumption stated), <strong>decisions recorded</strong>, and your <strong>override rate</strong>.",
            "A <strong>crop-stress map</strong>: a coloured heat tile per field (greener is healthier, amber means falling), plus an optional satellite map with your fields pinned.",
            "A soil-moisture bar for each field against its water-now line.",
            "A <strong>timeline</strong> of what we advised and what you did, newest first.",
        ],
        "does": [
            "Open any field from here.",
            "Spot a field whose greenness is falling before it shows on the leaves.",
        ],
        "tip": "The heat tiles work offline. The satellite map needs internet.",
    },
    {
        "id": "s-alerts", "icon": "bell", "where": "Alerts tab (bell icon)",
        "title": "Alerts: we tell you before it becomes a problem",
        "purpose": "Short messages about things that need you, so you do not have to keep checking.",
        "sees": [
            "<strong>Morning plan</strong>: one line per field, for example <em>Maize: skip, rain likely.</em>",
            "<strong>Crop stress</strong> alerts when greenness falls, <strong>heavy rain</strong> alerts, and <strong>out-of-date data</strong> alerts when a reading or forecast is old.",
            "A badge on the bell and the Alerts tab shows how many are new.",
            "<strong>Alert settings</strong>: switches for in-app, SMS and WhatsApp, and <strong>quiet hours</strong>.",
            "<strong>Sent messages</strong>: a log of what would be sent by SMS or WhatsApp. In this version nothing leaves the app.",
        ],
        "does": [
            "Mark everything as read.",
            "Choose which channels you want and when we should stay quiet. Urgent crop-stress alerts can still come through at night.",
        ],
        "tip": None,
    },
    {
        "id": "s-plans", "icon": "card", "where": "Account &rarr; Plans and billing",
        "title": "Plans and billing",
        "purpose": "See your trial, compare plans priced in Naira, and change plan. Prices follow the size of your farm and the number of fields.",
        "sees": [
            "Your <strong>current plan</strong>, days left in the trial, and how many fields and hectares you are using.",
            "Plan cards: <strong>Starter</strong>, <strong>Farm</strong> and <strong>Partner</strong>, each with its price per month, limits and what it includes.",
            "An <strong>invoice history</strong> table.",
        ],
        "does": [
            "Choose or switch a plan.",
            "Adding a field beyond your plan's limit takes you here to choose a bigger one.",
        ],
        "tip": "This version is in <strong>test mode</strong>. No real money is taken and no card details are collected.",
    },
    {
        "id": "s-pilot", "icon": "chart", "where": "Account &rarr; Pilot results",
        "title": "Pilot results",
        "purpose": "A simple summary of how the advice has worked on your farm, to share with your cooperative or the pilot team.",
        "sees": [
            "Per farm: number of fields, decisions recorded, how often you overrode the advice, and an estimate of water saved.",
            "A short feedback form with a 1 to 5 rating and a note.",
        ],
        "does": ["Tell us what worked and what should be fixed."],
        "tip": None,
    },
    {
        "id": "s-account-page", "icon": "settings", "where": "Account tab",
        "title": "Account and display",
        "purpose": "Your settings, and how the app looks and moves on your device.",
        "sees": [
            "Shortcuts to plans, pilot results, alert settings, sent messages and adding another farm.",
            "<strong>Display &rarr; Animation and movement</strong>: choose <em>Follow my device</em>, <em>Reduce motion</em> or <em>Full animation</em>. Reduce motion makes buttons, cards and charts fade instead of move, and stops numbers counting up.",
            "<strong>Sensor API keys</strong> for a future soil sensor or gateway to send readings automatically.",
            "<strong>Sign out</strong>.",
        ],
        "does": [
            "Turn movement down if animation bothers you or your phone is slow. The choice is saved on that device.",
            "Create or delete an API key for a sensor.",
        ],
        "tip": "Everything in the app works the same with motion reduced. Motion is only ever decoration, never the only way information is shown.",
    },
    {
        "id": "s-partner", "icon": "users", "where": "Partner and System (only for partner and admin accounts)",
        "title": "Partner dashboard and System",
        "purpose": "For cooperatives, agricultural organisations and irrigation providers who support many farms, and for the people who run the service.",
        "sees": [
            "<strong>Partner dashboard</strong>: farms in your organisation with fields, decisions, override rate, water saved and <strong>data-quality flags</strong> such as old soil readings. Pilot feedback appears below.",
            "<strong>System</strong> (admins): whether weather, satellite and the AI assistant are working, the list of users, plans, and <strong>pilot codes</strong> you can create.",
        ],
        "does": [
            "Create a pilot code and give it to farmers so they join under your organisation with a longer trial.",
            "See which farms need a nudge to enter fresh readings.",
        ],
        "tip": "A partner only ever sees the farms linked to their own organisation.",
    },
    {
        "id": "s-demo", "icon": "play", "where": "Demo controls and the judge walkthrough (sample farm only)",
        "title": "Demo controls",
        "purpose": "Built so a short live demo can show the system reacting. Appears only on the sample farm and is labelled <strong>Demo data</strong>.",
        "sees": [
            "A <strong>scenario switch</strong>: Normal day, Rainy day, Dry spell.",
            "<strong>Simulate sensor reading</strong>, which adds a labelled simulated soil reading.",
            "A <strong>guided walkthrough</strong> that steps through the problem, a decision, Why this?, override, ask a question and the partner view.",
        ],
        "does": [
            "Switch to <em>Rainy day</em>: the maize and cassava skip, and the tomato bed becomes <em>Watch</em> because greenness is falling in wet soil.",
            "Switch to <em>Dry spell</em>: all three fields call for water, and you can see the amounts and the best time.",
            "<em>Reset demo</em> rebuilds the sample farm from scratch.",
        ],
        "tip": None,
    },
]

GLOSSARY = [
    ("Soil moisture (%)", "How wet the soil is, as a share of its volume. A reading of 25% means a quarter of the soil volume is water."),
    ("Water-now line", "The moisture level below which your crop starts to feel thirsty. When the soil falls under it, we say water."),
    ("Field capacity", "The most water the soil can hold against gravity. After a good soak and drainage, soil sits at about this level."),
    ("Waterlogged", "So wet that roots cannot get air. Do not add water, and check drainage."),
    ("mm of water", "Depth of water. One millimetre over one square metre is one litre, so 10 mm on a 100 m² bed is 1,000 litres."),
    ("Evapotranspiration", "Water the crop and soil lose to the air on a hot day. The hotter and windier, the more your crop drinks."),
    ("Crop coefficient (Kc)", "How much water this crop uses at its current stage compared with grass. A bigger Kc means a thirstier stage."),
    ("NDVI (crop stress)", "A number from 0 to 1 for how green and healthy the crop looks from space. Falling greenness is an early warning."),
    ("Confidence", "How sure we are. It falls when a soil reading or the forecast is missing or old, and we tell you which."),
    ("Override", "Doing it your own way. We record it and learn, but never change anything without asking you."),
]


# ---- "How to use it": the practical half of the guide -------------------------------------------------------------

QUICKSTART = [
    ("Add your farm", "Open <strong>Fields</strong> and press <em>Add a farm</em>. Tap the map where your farm is (or press <em>Use my location</em>). This is how we get the weather for your exact spot.", "map-pin"),
    ("Add a field", "Give it a name, pick the crop, say how big it is, the soil type, the planting date and how you water. You do not need to know the growth stage. We work it out.", "sprout"),
    ("Take a soil reading", "Push a probe or your finger about 10 cm into the soil. On the field page, move the slider to what you find and press <em>Save reading</em>. This is the single most useful thing you can give us.", "thermo"),
    ("Read today's decision", "Go to <strong>Today</strong>. Each field has one card: water now, water later, skip, or watch, with how much and when.", "today"),
    ("Respond", "Press <strong>Accept advice</strong> if you agree. If you will do something different, press <strong>Override</strong> and tell us what. Both are saved.", "check"),
]

DAILY_ROUTINE = [
    ("Morning, 2 minutes", "Open <strong>Today</strong>. Look at each card's decision and time window. Accept or override.", "sunset"),
    ("When you water", "Use the amount shown. If you only have a few cans, ask <em>How much if I only have 5 cans?</em> on the field page.", "drop"),
    ("Every day or two", "Add a fresh soil reading on each field. Confidence goes up and the advice sharpens.", "thermo"),
    ("Once a week", "Open <strong>Insights</strong>. Check the crop-stress tiles for any field going amber, and see how much water you have saved.", "chart"),
    ("After harvest", "On the field page, add the harvest in kilograms and tick the box if a dry spell hurt it. Next season starts smarter.", "leaf"),
]

SITUATIONS = [
    ("The confidence says Low", "Something is missing or old. The card tells you what. Usually the fix is a fresh soil reading, or the forecast needs a few minutes to refresh. The advice is still our best estimate.", "alert"),
    ("It says Watch and I expected to water", "Watch means more water will not fix the problem. The crop is losing greenness but the soil is already wet. Look for disease, pests, poor drainage or a nutrient problem, and add a soil reading.", "eye"),
    ("It says Skip but the leaves look dry", "Trust your eyes. Press <strong>Override</strong>, choose <em>Water this field</em>, and pick the reason <em>Crop looks thirsty</em>. Also add a soil reading. It may be drier than we think.", "pencil"),
    ("It wants a lot of water", "A single watering is capped at 30 mm because more mostly runs off. Give that amount now and check again tomorrow. We say so on the card.", "drop"),
    ("Rain is forecast but I am not sure", "Open <strong>Why this?</strong>. We count only part of the forecast rain, and we show the chance as a number, not just a picture. <em>What if I wait a day?</em> tells you the cost of waiting.", "cloud-rain"),
    ("I have no internet", "Pages you opened before are still on your phone, marked with when they were last updated. Soil readings and questions need a connection.", "wifi-off"),
    ("Movement or animation bothers me", "Go to <strong>Account &rarr; Display</strong> and choose <em>Reduce motion</em>. Everything works the same.", "settings"),
]

TOC_GUIDE = [
    ("start", "Your first 5 minutes"), ("daily", "A daily routine"), ("decisions", "The four decisions"), ("situations", "When something looks off"),
    ("screens", "Every screen"),
] + [(s["id"], s["title"]) for s in SCREENS] + [("words", "Words you will meet"), ("honest", "What we are honest about")]
