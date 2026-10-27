"""Master cue sheet: the single source of timing for picture and sound (seconds)."""

TITLE = 'WHAT WILL PEOPLE SAY?'
DURATION = 160.0

# Music sections (start, end). The grind and the release run at 120 BPM (one bar = 2 s).
MUSIC = {
    'joy': (0.0, 14.0),        # his song on nylon guitar, cut off mid-phrase
    'eyes': (14.0, 22.0),      # drone, heartbeat, whispers
    'years': (22.0, 40.0),     # sad piano ostinato, ticking clock
    'mirror': (40.0, 50.0),    # dissonant string swell, glass crack
    'bottom': (50.0, 60.0),    # solo piano, his theme in minor
    'day1': (60.0, 70.0),      # near silence -> riser
    'grind': (70.0, 110.0),    # drums, bass, strings, the theme
    'fight': (110.0, 120.0),   # tension, roar, a breath of silence
    'release': (120.0, 136.0), # full band and choir, then warm resolve
    'callback': (136.0, 148.0),# his song again, finished this time
    'title': (148.0, 160.0),   # pad and last chord
}
BPM_GRIND = 120

# Narrator captions: (text, start, end)
NARRATOR = [
    ('He had a song in him.', 1.0, 4.8),
    ('But he only ever played it alone.', 7.4, 12.2),
    ('He let them decide.', 50.8, 53.6),
    ('Year after year.', 54.0, 56.4),
    ('But dreams don’t wait for permission.', 56.8, 59.8),
    ('Most people weren’t even watching.', 125.6, 129.4),
    ('The ones who were...', 129.8, 132.2),
    ('...needed to see someone try.', 132.4, 135.8),
]

# The shadow crowd's whispers: (text, start, end, voice style)
WHISPERS = [
    ('cringe.', 15.0, 17.0, 'hiss'),
    ('who does he think he is?', 16.6, 19.2, 'deep'),
    ("everyone's gonna laugh.", 18.6, 21.0, 'hiss'),
    ('you? on stage?', 23.6, 25.6, 'deep'),
    ("don't embarrass yourself.", 25.4, 27.6, 'hiss'),
    ('stay quiet.', 42.0, 44.2, 'deep'),
    ('know your place.', 44.4, 46.8, 'deep'),
    ('cringe.', 72.5, 73.4, 'hiss'),
    ('nobody cares.', 91.6, 92.5, 'deep'),
    ('embarrassing.', 93.2, 94.1, 'hiss'),
    ('quit.', 94.8, 95.7, 'deep'),
]
ROAR = ('WHAT WILL PEOPLE SAY?', 114.0, 116.6)

# Top-left counters: (label, start, end)
COUNTERS = [
    ('AGE 16', 22.3, 28.8),
    ('AGE 17', 29.0, 30.8), ('AGE 19', 30.8, 32.6), ('AGE 22', 32.6, 34.4),
    ('AGE 25', 34.4, 36.2), ('AGE 27', 36.2, 38.0), ('AGE 29', 38.0, 39.9),
    ('DAY 1.', 62.0, 69.6),
    ('DAY 3', 70.0, 76.0), ('DAY 12', 76.0, 82.0), ('DAY 40', 82.0, 90.0), ('DAY 64', 90.0, 98.0),
    ('DAY 90', 98.0, 100.0), ('DAY 120', 100.0, 102.0), ('DAY 150', 102.0, 104.0),
    ('DAY 180', 104.0, 106.0), ('DAY 210', 106.0, 108.0), ('DAY 240', 108.0, 110.0),
]

# Key story events used by both picture and sound
EV = {
    'snap': 14.0,             # his song is cut off
    'notes_fall': 14.15,
    'eyes_open': [14.35, 14.7, 15.05, 15.35, 15.7, 16.0, 16.35, 16.7, 17.1, 17.5],
    'guitar_down': 20.2,
    'pen_down': 26.5,
    'walk_away': 27.3,
    'montage_cuts': [29.0, 30.8, 32.6, 34.4, 36.2, 38.0],
    'crack': 47.0,
    'look_up': 58.6,
    'blow': 61.5,
    'twang': 63.6,
    'rec': 65.6,
    'eyes_return': [66.0, 66.3, 66.6, 66.9, 67.2],
    'tap_post': 69.5,
    'drop': 70.0,
    'ding_lol': 76.6,
    'phone_down': 78.6,
    'coin': 87.5,
    'curtain': 110.0,
    'eye_wave': 112.6,
    'breath': 118.0,
    'strum': 120.0,
    'lights_up': 124.0,
    'glance': 142.6,          # he looks at the tiny shadow; it gives up
    'title_card': 148.0,
}

# The opening scene's guitar strums at 80 BPM, eighth notes
JOY_BPM = 80
