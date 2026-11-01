"""Master cue sheet for 'He's Waiting.': the single source of timing for picture and sound (seconds).

The old man's pocket watch ticks once a second for the whole film, so every cut can sit on a tick. The scrolling
loop is an 80 BPM lo-fi groove (one bar = 3 s = three ticks against four beats); the old man's theme is in 6/8
with the dotted quarter on the tick (one bar = 2 s), so from Day 1 on the clock becomes the music's pulse.
"""

TITLE = 'HE’S WAITING.'
DURATION = 212.0
TICK = 1.0
LOFI_BPM = 80

MUSIC = {
    'hook': (0.0, 19.4),        # tinny clips from the phone; the watch fades in; a low organ under the reveal
    'title': (19.4, 23.0),      # organ chord and the tick
    'loop': (23.0, 43.0),       # the lo-fi groove, each night more worn; the time-lapse speeds the tape up
    'mirror': (43.0, 57.0),     # tape stop; clarinet and organ, a cluster; the shadow's drone
    'avoid': (57.0, 67.0),      # the groove leaking from his headphones, hollow; the tick slows
    'bottom': (67.0, 92.6),     # the watch stops: silence; the line; a lone clarinet; black; a heartbeat; a tick
    'day1': (92.6, 111.0),      # the old man's theme, slow, on the tick: vibraphone, clarinet, organ
    'climb': (111.0, 135.0),    # 6/8 on the tick: marimba clockwork, claps, bass; the theme on voices
    'temptation': (135.0, 145.0),  # rain and the alarm; the lo-fi tries to come back, warped; "He doesn't."
    'rise': (145.0, 157.0),     # the drop: drums; the theme in full
    'ascent': (157.0, 172.0),   # organ and drums climbing; a key change at the top
    'sunrise': (172.0, 189.0),  # full organ, voices and bells; thinning to the clarinet as he fades
    'alone': (189.0, 193.0),
    'epilogue': (193.0, 203.0),  # the theme on vibraphone; the watch on the nightstand
    'title_card': (203.0, 212.0),
}

# Calm narrator captions: (text, start, end)
NARRATOR = [
    ('Every night, he’s there.', 5.0, 7.6),
    ('That’s him. Fifty years from now.', 9.0, 11.9),
    ('Every day he wastes,', 12.3, 14.0),
    ('the old man gets weaker.', 14.1, 16.0),
    ('One day you’ll meet him.', 195.6, 199.0),
    ('Make sure he’s proud.', 199.4, 202.8),
]

# The shadow's whispers: (text, start, end, voice style)
WHISPERS = [
    ('you have time.', 16.8, 18.4, 'soft'),
    ('one more video.', 24.0, 25.7, 'close'),
    ('start tomorrow.', 29.6, 31.2, 'close'),
    ('you’re still young.', 33.9, 35.6, 'close'),
    ('you’re just tired.', 54.2, 56.0, 'close'),
    ('you have all the time in the world.', 58.2, 61.4, 'soft'),
    ('you have time.', 68.4, 70.0, 'soft'),
    ('you have time.', 138.6, 140.2, 'close'),
]

# The time-lapse: the same whisper again and again, faster and faster (one subtitle covers them all)
CHORUS = [37.2, 38.3, 39.2, 39.9, 40.5, 41.0, 41.4]
SUBTITLES_EXTRA = [(37.2, 41.9, 'You have time. You have time. You have time…')]

# Spoken lines: (text, start, end, who)
SPEECH = [
    ('I waited for you…', 81.4, 83.6, 'old'),
    ('…my whole life.', 84.4, 86.8, 'old'),
    ('He doesn’t.', 141.8, 143.0, 'hero'),
]

# Top-left counters: (label, start, end)
COUNTERS = [
    ('2:47 AM', 0.9, 7.6),
    ('TUE 3:12 AM', 23.2, 27.5),
    ('1:04 PM', 27.6, 29.0),
    ('WED 3:40 AM', 29.1, 32.0),
    ('5:52 PM', 32.1, 33.5),
    ('THU 4:05 AM', 33.6, 36.5),
    ('1:20 PM', 43.2, 45.6),
    ('MON 3:58 AM', 57.2, 60.6),
    ('4:12 AM', 67.2, 70.6),
    ('DAY 1', 93.0, 98.0),
    ('DAY 3', 111.2, 115.0),
    ('DAY 12', 115.2, 119.0),
    ('DAY 30', 119.2, 123.0),
    ('DAY 48', 123.2, 127.0),
    ('DAY 77', 127.2, 131.0),
    ('DAY 101', 135.2, 139.0),
    ('DAY 180', 145.1, 147.0),
    ('DAY 240', 147.1, 149.0),
    ('DAY 300', 149.1, 151.0),
    ('DAY 330', 151.1, 153.0),
    ('DAY 365', 153.2, 157.0),
    ('2:47 AM', 193.6, 197.0),
]

# How strong the old man is (0 = dying, 1 = full of life), keyed in time; picture and sound both read it
VITALITY = [
    (0.0, 0.42), (12.4, 0.42), (15.6, 0.34), (23.0, 0.32), (29.0, 0.27), (33.5, 0.22), (36.5, 0.2), (42.0, 0.12),
    (57.0, 0.09), (67.0, 0.05), (72.2, 0.0), (92.6, 0.02), (101.0, 0.06), (106.0, 0.13), (111.0, 0.17),
    (115.0, 0.27), (119.0, 0.37), (123.0, 0.46), (127.0, 0.58), (135.0, 0.66), (145.0, 0.74), (149.0, 0.8),
    (151.0, 0.85), (153.0, 0.9), (172.0, 0.96), (174.0, 1.0),
]

# Key story events used by both picture and sound
EV = {
    # the hook
    'swipes': [0.7, 1.5, 2.1, 3.3, 4.6, 6.0, 7.1, 8.3, 10.2, 12.6, 14.4, 16.0],
    'tick_in': 1.0,             # the watch becomes audible
    'figure': 4.0,              # the figure at the foot of the bed is in frame
    'head_up': 5.2,             # he lifts his head toward the boy
    'flare': 9.4,               # a bright clip lights the old man's face
    'chuckle': 12.6,            # the boy laughs at something on the phone
    'drain': [12.7, 14.4, 15.4],  # each laugh and swipe pulls a little light out of the old man
    'cough': 15.0,
    'eyes_open': 16.2,          # red eyes in the corner behind the headboard
    'title': 19.4,
    # the loop
    'nights': [23.0, 29.0, 33.5],
    'coughs': [26.4, 31.4, 35.9],
    'snooze': 28.0,             # he slaps the alarm and turns over
    'note_falls': 32.6,         # a goal sticky note drops off the wall
    'timelapse': (36.5, 42.0),
    'stop': 42.0,               # the time-lapse slams to a halt
    # the mirror
    'mirror': 43.0,
    'spit': 45.0,
    'old_in_mirror': 46.0,
    'stop_brush': 48.2,
    'look': 49.0,
    'palm': 50.0,
    'step_back': 51.2,
    'blink': 52.0,
    'normal': 52.6,
    'shade_mirror': 53.8,
    'light_off': 56.4,
    # avoiding him
    'avoid': 57.0,
    'reach': (59.4, 62.0),
    'drop_hand': 62.2,
    'watch_slow': [63.0, 64.0, 65.2, 66.6],
    # rock bottom
    'slump': 67.0,
    'last_ticks': [68.0, 69.1, 70.4, 72.2],
    'watch_stops': 72.2,        # the next tick never comes
    'lower_phone': 73.4,
    'sit_up': 75.8,
    'old_lifts': 78.8,
    'tear': 88.0,
    'phone_dies': 89.6,
    'black': 90.6,
    'heartbeats': [90.9, 91.75],
    'tick_back': 92.0,          # one tick in the dark
    # Day 1
    'dawn': 92.6,
    'stand1': 97.4,
    'curtains': 100.2,
    'old_wakes': 101.0,
    'shoes': 102.4,
    'rise': 105.2,              # he stands, and the old man stands with him, a little straighter
    'out': 107.0,
    'door_open': 107.6,
    # the climb
    'days': [111.0, 115.0, 119.0, 123.0, 127.0],
    'drawer': 120.4,            # the phone goes in the drawer
    'tuck': 121.4,              # the old man pulls the blanket over the boy's feet
    'jog_look': 130.6,          # the boy looks back: the old man is jogging behind him
    'wave': 131.6,
    # the last temptation
    'temptation': 135.0,
    'alarm': 135.4,
    'shade_rises': 137.0,
    'look_door': 140.4,
    'he_doesnt': 141.8,
    'up_through': 143.2,
    'shade_gone': 143.6,
    'drop': 145.0,
    'quick_days': [145.0, 147.0, 149.0, 151.0],
    # the summit
    'trailhead': 153.0,
    'nod': 155.2,
    'set_off': 156.0,
    'ascent': 157.0,
    'last_step': 167.0,
    'hand_offer': 169.0,
    'pull_up': 169.8,
    'on_top': 171.4,
    'sunrise': 172.0,
    'sun_breaks': 173.0,
    'look_proud': 175.4,
    'watch_give': (177.0, 179.6),
    'shoulder': (180.2, 182.4),
    'fade': (183.0, 188.6),
    'alone': 189.0,
    # the end
    'epilogue': 193.0,
    'title_card': 203.0,
}

# The title drop and the closing card: (text, start, end)
TITLE_CARD = [
    ('HE’S WAITING.', 19.7, 22.6),
    ('HE’S WAITING.', 203.4, 211.6),
]
