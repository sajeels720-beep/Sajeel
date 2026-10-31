"""Master cue sheet: the single source of timing for picture and sound (seconds).

The film runs on a 120 BPM grid (one bar = 2 s): the January groove, the vanishing (one quitter and one
instrument lost every two bars), the year-long grind and the callback all land on bar lines.
"""

TITLE = 'EVERYONE QUITS IN FEBRUARY.'
DURATION = 160.0
BPM = 120

MUSIC = {
    'count': (0.0, 6.0),          # 3, 2, 1: ticking, a riser, the crowd shouting; fireworks
    'january': (6.0, 20.0),       # the full, bright January groove: everybody is here
    'vanish': (20.0, 44.0),       # one instrument leaves with every quitter
    'february': (44.0, 58.0),     # a lonely piano in E minor; the tap
    'photos': (58.0, 72.0),       # the old man's theme on a music box, then cello
    'lift': (72.0, 74.0),         # the riser under the bar
    'year': (74.0, 102.0),        # the drop: the grind through the seasons
    'goodbye': (102.0, 106.0),    # the old man's pat on the shoulder
    'december': (106.0, 122.0),   # a soft, sweet temptation; the refusal; midnight
    'callback': (122.0, 148.0),   # Jan 1 again: the groove comes back, warm
    'title': (148.0, 160.0),
}

# Calm narrator captions: (text, start, end)
NARRATOR = [
    ('Every January, everyone starts.', 10.2, 13.8),
    ('By February, almost everyone was gone.', 44.6, 48.4),
    ('Same corner. Every year.', 60.4, 63.4),
    ('Everyone starts.', 141.6, 144.0),
    ('Almost nobody stays.', 144.4, 147.3),
]

# The shadow's whispers: (text, start, end, voice style)
WHISPERS = [
    ('you’re sore.', 21.1, 22.9, 'hiss'),
    ('start again monday.', 25.1, 26.9, 'deep'),
    ('nobody’s watching.', 29.1, 30.9, 'hiss'),
    ('it’s not working.', 33.1, 34.9, 'deep'),
    ('skip today.', 37.1, 38.9, 'hiss'),
    ('you deserve a rest.', 41.1, 42.9, 'deep'),
    ('everyone quit.', 50.0, 52.0, 'deep'),
    ('go home.', 52.8, 54.2, 'hiss'),
    ('too cold.', 82.8, 84.3, 'hiss'),
    ('too hot.', 87.8, 89.2, 'deep'),
    ('you’ve done enough.', 110.8, 113.2, 'soft'),
    ('rest now.', 114.3, 115.8, 'soft'),
]

# The New Year countdown, shouted by a crowd: (word, time)
COUNTDOWN = [('THREE!', 1.0), ('TWO!', 2.0), ('ONE!', 3.0), ('HAPPY NEW YEAR!', 4.0)]

# Top-left date counters: (label, start, end)
COUNTERS = [
    ('JAN 1', 4.3, 20.0),
    ('JAN 4', 20.0, 24.0), ('JAN 9', 24.0, 28.0), ('JAN 15', 28.0, 32.0), ('JAN 21', 32.0, 36.0),
    ('JAN 28', 36.0, 40.0), ('FEB 3', 40.0, 44.0),
    ('FEB 12.', 44.0, 58.0),
    ('FEB 20', 78.0, 80.0), ('MAR 2', 80.0, 82.0),
    ('MAR', 82.0, 84.0), ('APR', 84.0, 85.3), ('MAY', 85.3, 86.6), ('JUN', 86.6, 87.7), ('JUL', 87.7, 88.7),
    ('AUG', 88.7, 89.8), ('SEP', 89.8, 90.8), ('OCT', 90.8, 92.4), ('NOV', 92.4, 98.0),
    ('DEC', 98.0, 102.0), ('DEC 24', 102.0, 106.0),
    ('DEC 31.', 106.0, 122.0),
    ('JAN 1.', 122.0, 139.6),
]

# The gym's New Year photos on the wall by the door
PHOTO_YEARS = [1986, 1996, 2006, 2016, 2026]
NEW_PHOTO_YEAR = 2027

# Key story events used by both picture and sound
EV = {
    # midnight
    'count': [1.0, 2.0, 3.0],
    'midnight': 4.0,
    'bursts': [(4.0, 700, 300, 0), (4.35, 1260, 250, 1), (4.7, 980, 190, 2), (5.05, 430, 360, 3),
               (5.35, 1530, 330, 4), (5.6, 820, 420, 5)],
    'volley': [(4.0, 300, 300, 6), (4.05, 1620, 280, 7), (4.12, 980, 150, 8), (4.22, 600, 430, 9),
               (4.3, 1320, 420, 10), (4.45, 140, 400, 11), (4.55, 1800, 180, 12)],
    # January 1st
    'doors': 6.2,               # the gym doors burst open and the crowd floods in
    'gym_wide': 9.0,
    'hero_close': 14.0,
    'photo_call': 16.4,         # everyone turns to the camera and poses
    'photo_flash': 18.0,
    # the vanishing: one cut per day, two bars each; offsets inside a day
    'days': [20.0, 24.0, 28.0, 32.0, 36.0, 40.0],
    'tap': 1.0,                 # the shadow's finger lands on a shoulder
    'quit': 1.5,                # they start to go to smoke
    # February 12th
    'feb': 44.0,
    'sit_down': 48.6,
    'tap_hero': 49.6,
    'hand_up': 52.0,
    'smoke': 52.4,
    'stand_up': 54.4,
    'walk_out': 55.0,
    'stop': 57.6,               # the photos by the door stop him
    # the photos and the old man
    'photos': 58.0,
    'turn': 63.6,
    'nod': 65.6,
    'hand_back': 67.2,          # the smoke stops; his fingers come back
    'fist': 68.2,
    'shrug': 69.0,              # he shrugs the shadow's hand off
    'drop_bag': 70.2,
    # the bench
    'lie_down': 72.0,
    'push': 73.0,
    'drop': 74.0,               # lockout; the beat drops
    # the year
    'struggle': [78.0, 80.0],
    'run': (82.0, 94.0),
    'shade_snow': 83.6,
    'shade_summer': 87.4,
    'strong': [94.0, 96.0, 98.0, 100.0],
    'pat': 103.4,               # the old man's hand on his shoulder
    'old_leaves': 104.2,
    # December 31st
    'dec': 106.0,
    'shade_sits': 110.0,
    'hand_smoke2': 114.0,
    'towel': 116.0,
    'stand2': 118.2,
    'chalk': 119.0,
    'lift2': 120.0,
    'shade_gone': 120.5,
    'midnight2': 122.0,
    # January 1st again
    'doors2': 124.2,
    'corner': 127.0,
    'newcomer': 132.0,
    'nod2': 136.4,
    'step_in': 137.4,
    'proud': 139.0,
    'photo_call2': 139.6,
    'photo_flash2': 140.8,
    'photo_wall': 143.2,
    'title_card': 148.0,
}

DAY_FLASH = EV['days'][1:]

# The title card's lines: (text, start, end)
TITLE_CARD = [
    ('EVERYONE QUITS IN FEBRUARY.', 148.4, 159.6),
    ('Be the one who stays.', 151.0, 159.6),
]
