"""Master cue sheet: the single source of timing for picture and sound (seconds)."""

TITLE = '90 DAYS LEFT.'
DURATION = 160.0

# Music sections (start, end). The grind and the release run at 120 BPM (one bar = 2 s), in D minor / F major.
MUSIC = {
    'tick': (0.0, 9.0),         # clock ticks, a music-box motif, the phone's first buzz
    'lapse': (9.0, 22.0),       # pizzicato loop over the time-lapse, sticky notes slapping on
    'sink': (22.0, 30.0),       # alarm, then a low detuned drone as the bed swallows him
    'mountain': (30.0, 40.0),   # piano ostinato that keeps climbing with the book pile
    'low': (40.0, 50.0),        # the shadow rises out of the phone; drone, heartbeat, silence
    'father': (50.0, 62.0),     # 5 AM: the father theme on cello and piano
    'day1': (62.0, 70.0),       # the drawer, the lock, the bangs, a riser, the drop
    'grind': (70.0, 108.0),     # piano ostinato, staccato strings, taiko, the theme
    'exam': (108.0, 120.0),     # the exam hall: clock, heartbeat, the roar, a breath of silence
    'release': (120.0, 136.0),  # the theme in F major, full and warm
    'callback': (136.0, 148.0), # 5 AM again: the father theme, in major this time
    'title': (148.0, 160.0),    # last chords
}

# Narrator captions: (text, start, end)
NARRATOR = [
    ('Plenty of time, he thought.', 1.2, 4.4),
    ('Every day he wasted...', 56.6, 59.0),
    ('...someone else paid for.', 59.2, 61.8),
    ('The result was written...', 129.8, 132.4),
    ('...on the days nobody saw.', 132.6, 135.8),
]

# The phone shadow's whispers: (text, start, end, voice style)
WHISPERS = [
    ('just five minutes.', 6.6, 8.6, 'hiss'),
    ('you have time.', 11.8, 13.6, 'deep'),
    ('start tomorrow.', 16.0, 17.8, 'hiss'),
    ('one more video.', 19.6, 21.4, 'hiss'),
    ('you deserve a break.', 25.0, 27.2, 'deep'),
    ('too late now.', 36.4, 38.6, 'deep'),
    ('you’re too far behind.', 42.0, 44.4, 'hiss'),
    ('why even try?', 44.8, 47.0, 'deep'),
    ('let me out!', 66.2, 67.8, 'hiss'),
    ('you’re not smart enough.', 83.6, 85.6, 'deep'),
    ('you’ll go blank.', 110.0, 112.0, 'hiss'),
]
ROAR = ('YOU’LL GO BLANK.', 114.0, 116.6)

# Top-left counters: (label, start, end)
COUNTERS = [
    ('90 DAYS LEFT.', 0.8, 9.0),
    ('89 DAYS LEFT', 9.0, 11.6), ('86 DAYS LEFT', 11.6, 14.2), ('82 DAYS LEFT', 14.2, 16.8),
    ('77 DAYS LEFT', 16.8, 19.4), ('71 DAYS LEFT', 19.4, 22.0),
    ('60 DAYS LEFT', 22.0, 30.0),
    ('45 DAYS LEFT', 30.0, 32.0), ('38 DAYS LEFT', 32.0, 34.0), ('30 DAYS LEFT.', 34.0, 49.4),
    ('29 DAYS LEFT.', 62.4, 69.8),
    ('27 DAYS LEFT', 70.0, 76.0), ('24 DAYS LEFT', 76.0, 82.0), ('19 DAYS LEFT', 82.0, 88.0),
    ('14 DAYS LEFT', 88.0, 96.0), ('11 DAYS LEFT', 96.0, 98.0), ('8 DAYS LEFT', 98.0, 100.0),
    ('5 DAYS LEFT', 100.0, 102.0), ('3 DAYS LEFT', 102.0, 104.0), ('2 DAYS LEFT', 104.0, 106.0),
    ('1 DAY LEFT', 106.0, 108.0),
    ('0 DAYS LEFT.', 108.2, 113.0),
    ('RESULT DAY.', 122.4, 126.4),
]

# Key story events used by both picture and sound
EV = {
    # the desk at night
    'book_open': 1.6,
    'buzz': [2.8, 5.4],
    'glance': 3.2,
    'flip': 6.1,              # he turns the phone over: two red eyes in the screen
    'pickup': 7.6,
    # the time-lapse: each cut is a new day; a sticky note slaps on, a book thuds onto the pile
    'lapse_cuts': [9.0, 11.6, 14.2, 16.8, 19.4],
    'note_slap': 0.7,         # offset into each lapse day
    'book_thud': 1.5,
    # the quicksand bed
    'alarm': 22.3,
    'sit_up': 23.0,
    'sink': 24.0,
    'sunk': 27.6,
    # the mountain of books
    'mountain_cuts': [30.0, 32.0, 34.0],
    'reach': 35.0,
    'wobble': 35.5,
    'flop': 39.0,             # he drops face-down on the bed
    # the low point
    'rise': 41.0,             # the shadow climbs out of the phone
    'curl': 45.6,
    'blackout': 49.2,
    # 5 AM
    'clock_5am': 50.3,
    'son_door': 51.2,
    'tape': 53.6,
    'stand': 56.4,
    'light_off': 58.4,
    'door_close': 59.9,
    # Day 1
    'grab_phone': 62.8,
    'drawer_open': 63.2,
    'drop_phone': 63.7,
    'slam': 64.3,
    'lock': 65.0,
    'bangs': [66.0, 66.6, 67.3],
    'book_pull': 68.0,
    'lamp_on': 68.9,
    'drop': 70.0,
    # the grind
    'bang_ignored': 72.4,
    'alarm2': 76.2,
    'break_free': 77.8,
    'fail': 82.4,             # a practice test comes back: 42%
    'look_door': 85.6,        # the father's taped shoes by the door
    'pencil_up': 87.0,
    'father_peek': 90.6,
    'father_smile': 92.6,
    'scores': [98.0, 100.0, 102.0],
    'drawer_quiet': 104.0,
    'stack_done': 106.0,
    # the exam hall
    'sit': 108.3,
    'shade_sits': 108.9,
    'paper_flip': 111.0,
    'blank': 112.4,
    'roar': 114.0,
    'eyes_shut': 116.6,
    'memories': [117.0, 117.45],
    'breath': 117.9,
    'eyes_open': 118.6,
    'write': 119.2,
    'release': 120.0,
    'shade_gone': 120.8,
    # result day
    'open_result': 124.0,
    'turn_screen': 125.4,
    'father_reads': 126.0,
    'tears': 127.6,
    'shoulder': 129.0,
    # 5 AM again
    'shoes_seen': 139.4,
    'note_read': 140.6,
    'father_turns': 142.2,
    'door_sun': 144.4,
    'title_card': 148.0,
}

# The opening's clock and the time-lapse loop
TICK_BPM = 60
GRIND_BPM = 120

# A soft exposure flash on every time-lapse and countdown cut
LAPSE_FLASH = EV['lapse_cuts'][1:] + EV['mountain_cuts'][1:]
