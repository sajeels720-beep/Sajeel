"""Master cue sheet for 'He's Waiting.': the single source of timing for picture and sound (seconds).

The old man's pocket watch ticks once a second for the whole film, so every cut can sit on a tick. His theme is in
6/8 with the dotted quarter on the tick (one bar = 2 s), so from Day 1 on the clock becomes the music's pulse.
"""

TITLE = 'HE’S WAITING.'
DURATION = 212.0
TICK = 1.0

# The story, for anyone reading the cues: he never looks up from his phone, so he never sees the old man (himself
# at 75) who sits at the foot of his bed every night and fades with every wasted day. At 4:12 AM the watch stops and
# the phone dies; in the black glass his own face is the old man's; he looks up and, for the first time, sees him.
# "I'm you." The old man looks at the poster on the wall, ONE DAY.: "One day never came." "I waited for you... my
# whole life." At dawn the boy crosses out ONE DAY. and writes DAY ONE.; the old man stands with him and lets his
# stick fall. From then on the boy does the work alone (every day he shows up, the old man gets stronger, unseen),
# until, on the poster's mountain at sunrise, the old man is there, waiting for him, strong. He gives him the watch
# and goes into the light.

MUSIC = {
    'hook': (0.0, 19.4),        # tinny clips from his phone over a low drone; the watch fades in; braams at the reveal
    'title': (19.4, 23.0),      # a braam and a low bell, on the tick
    'loop': (23.0, 43.0),       # the shadow's hypnotic loop, more worn each night; the time-lapse speeds it up like tape
    'mirror': (43.0, 57.0),     # dread: a stinger when the old man appears, a held cluster while he looks
    'avoid': (57.0, 67.0),      # the loop leaking from under the blanket; a slow heart in the drone; the tick slows
    'bottom': (67.0, 92.6),     # the watch stops: silence; the phone dies; a cold swell in the black glass; one hit;
                                # the theme alone on the English horn under the old man's words; black; a heart; a tick
    'day1': (92.6, 111.0),      # a low hit as ONE DAY. is crossed out; the theme on the tick once DAY ONE. is written
    'climb': (111.0, 135.0),    # 6/8 on the tick: a relentless synth-bass pulse, toms, the theme on horn, strings, voices
    'temptation': (135.0, 145.0),  # rain and the alarm; the shadow's loop tries to come back, warped; "He doesn't."
    'rise': (145.0, 157.0),     # the drop: braams, toms and the theme in full
    'ascent': (157.0, 172.0),   # a relentless build up the mountain
    'sunrise': (172.0, 189.0),  # D major at last: brass, voices and bells; thinning as he fades into the light
    'alone': (189.0, 193.0),
    'epilogue': (193.0, 203.0),  # night again: his words on a held chord, then hope
    'title_card': (203.0, 212.0),
}

# Calm narrator captions: (text, start, end)
NARRATOR = [
    ('Every night, he’s there.', 5.0, 7.2),
    ('He never looks up.', 7.3, 8.75),
    ('That’s him. Fifty years from now.', 8.85, 11.0),
    ('Everything he does today,', 11.15, 12.75),            # why he weakens: the old man is made of these days
    ('the old man has to live with.', 12.85, 14.6),
    ('Every day he wastes,', 14.75, 15.95),
    ('the old man gets weaker.', 16.05, 17.45),
    ('Every day he shows up,', 115.5, 117.3),
    ('the old man gets stronger.', 117.4, 119.4),
    ('One day you’ll meet him.', 195.6, 199.0),
    ('Make sure he’s proud.', 199.4, 202.8),
]

# The shadow's whispers: (text, start, end, voice style)
WHISPERS = [
    ('you have time.', 17.6, 19.15, 'soft'),
    ('one more video.', 24.0, 25.7, 'close'),
    ('start tomorrow.', 30.1, 31.6, 'close'),
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
# The characters never speak aloud: these are captions.
SPEECH = [
    ('I’m you.', 79.0, 80.8, 'old'),
    ('One day never came.', 81.9, 84.0, 'old'),
    ('I waited for you…', 84.8, 86.6, 'old'),
    ('…my whole life.', 87.0, 89.4, 'old'),
    ('He doesn’t.', 142.15, 143.3, 'hero'),
]

# Top-left counters: (label, start, end)
COUNTERS = [
    ('2:47 AM', 0.9, 7.6),
    ('TUE 3:12 AM', 23.2, 27.5),
    ('6:00 AM', 27.6, 29.0),
    ('WED 3:40 AM', 29.1, 32.0),
    ('5:52 PM', 32.1, 33.5),
    ('THU 4:05 AM', 33.6, 36.5),
    ('1:20 PM', 43.2, 45.6),
    ('MON 3:58 AM', 57.2, 60.6),
    ('4:12 AM', 67.2, 70.6),
    ('DAY 1', 96.4, 99.4),
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
    (57.0, 0.09), (67.0, 0.05), (70.4, 0.0), (92.6, 0.02), (101.0, 0.06), (106.0, 0.13), (111.0, 0.17),
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
    'eyes_open': 16.9,          # red eyes in the corner behind the headboard
    'title': 19.4,
    # the loop
    'nights': [23.0, 29.0, 33.5],
    'coughs': [26.4, 31.4, 35.9],
    'snooze': 28.0,             # 6:00 AM, RUN 5K: he slaps SNOOZE...
    'cane': 29.0,               # ...and the next night the old man needs a cane
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
    'last_ticks': [68.0, 69.1, 70.4],
    'watch_stops': 70.4,        # the next tick never comes
    'phone_dies': 72.2,         # 1%... and the screen goes black
    'reflection': 73.5,         # his face in the black glass becomes the old man's
    'turn': 76.2,               # he lowers the phone and, for the first time, looks up at him
    'sit_up': 76.4,
    'old_lifts': 77.4,
    'poster_look': 81.0,        # the old man looks up at the mountain poster: ONE DAY.
    'tear': 89.8,
    'black': 91.6,
    'heartbeats': [91.8],
    'tick_back': 92.0,          # one tick in the dark
    # Day 1
    'dawn': 92.6,
    'strike': 94.2,             # he crosses out ONE DAY. ...
    'write': 95.0,              # ... and writes DAY ONE.
    'stand1': 97.4,
    'curtains': 100.2,
    'old_wakes': 101.0,
    'shoes': 102.4,
    'rise': 105.2,              # he stands, and the old man stands with him, a little straighter...
    'cane_drop': 106.4,         # ...and lets his stick fall: he won't need it any more
    'out': 107.4,               # from here the boy does the work alone; the old man is not seen again until the top
    'door_open': 107.6,
    # the climb
    'days': [111.0, 115.0, 119.0, 123.0, 127.0],
    'drawer': 120.4,            # the phone goes in the drawer
    # the last temptation
    'temptation': 135.0,
    'alarm': 135.4,
    'shade_rises': 137.0,
    'look_spot': 140.4,         # he looks at the end of the bed, where the old man used to sit
    'he_doesnt': 142.15,
    'up_through': 143.2,
    'shade_gone': 143.6,
    'drop': 145.0,
    'quick_days': [145.0, 147.0, 149.0, 151.0],
    # the summit
    'trailhead': 153.0,
    'set_off': 156.0,
    'ascent': 157.0,
    'last_step': 167.0,
    'slip': 167.85,             # his foot slips off the edge...
    'push2': 170.0,             # ...he gets his breath back and goes again, alone
    'on_top': 171.3,
    'sunrise': 172.0,
    'sun_breaks': 173.0,
    'appear': 173.5,            # in the light at the edge of the summit: the old man, waiting for him
    'sees': 174.8,              # he lowers his hand from the sun and sees him
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
