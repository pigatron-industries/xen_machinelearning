
from typing import Tuple

# midi note numbers for percussion instruments
ACCOUSTIC_BASS_DRUM = 35
BASS_DRUM_1         = 36

SIDE_STICK          = 37
ACCOUSTIC_SNARE     = 38
HAND_CLAP           = 39
ELECTRIC_SNARE      = 40

LOW_FLOOR_TOM       = 41
HIGH_FLOOR_TOM      = 43
LOW_TOM             = 45
LOW_MID_TOM         = 47
HI_MID_TOM          = 48
HIGH_TOM            = 50

CLOSED_HI_HAT       = 42
PEDAL_HI_HAT        = 44
OPEN_HI_HAT         = 46

CRASH_CYMBAL_1      = 49
RIDE_CYMBAL_1       = 51
CHINESE_CYMBAL      = 52
RIDE_BELL           = 53
TAMBOURINE          = 54
SPLASH_CYMBAL       = 55
COWBELL             = 56
CRASH_CYMBAL_2      = 57
VIBRA_SLAP          = 58
RIDE_CYMBAL_2       = 59


class PercussionMap:
    """A map of percussion instruments to MIDI note numbers."""
    def __init__(self, map):
        self.map = map

    def __call__(self, midi:int) -> int|Tuple[int, float]|None:
        """Get the instrument group number for the given midi note number."""
        for group, instruments in self.map.items():
            for instrument in instruments:
                if isinstance(instrument, tuple):
                    if (instrument[0] == midi):
                        return group, instrument[1]
                else:
                    if (instrument == midi):
                        return group
        return None
    

SimplePercussionMap = PercussionMap({
        # bass drum
        0: [ACCOUSTIC_BASS_DRUM, BASS_DRUM_1],
        # snare
        1: [SIDE_STICK, ACCOUSTIC_SNARE, HAND_CLAP, ELECTRIC_SNARE], 
        # toms
        2: [LOW_FLOOR_TOM, HIGH_FLOOR_TOM, LOW_TOM, LOW_MID_TOM, HI_MID_TOM, HIGH_TOM],
        # hi-hat
        3: [CLOSED_HI_HAT, PEDAL_HI_HAT],
        4: [OPEN_HI_HAT],
        # cymbals
        5: [CRASH_CYMBAL_1, CHINESE_CYMBAL, RIDE_BELL, TAMBOURINE, SPLASH_CYMBAL, COWBELL, CRASH_CYMBAL_2, RIDE_CYMBAL_2],
})


ExtendedPercussionMap = PercussionMap({
        # bass drum 
        0: [ACCOUSTIC_BASS_DRUM, BASS_DRUM_1],
        # snare
        1: [SIDE_STICK, ACCOUSTIC_SNARE, HAND_CLAP, ELECTRIC_SNARE], 
        # toms
        2: [LOW_FLOOR_TOM],
        3: [HIGH_FLOOR_TOM],
        4: [LOW_TOM],
        5: [LOW_MID_TOM],
        6: [HI_MID_TOM],
        7: [HIGH_TOM],
        # hi-hat
        8: [CLOSED_HI_HAT, PEDAL_HI_HAT],
        9: [OPEN_HI_HAT],
        # cymbals
        10: [RIDE_CYMBAL_1, RIDE_CYMBAL_2, RIDE_BELL, TAMBOURINE, COWBELL],
        11: [CRASH_CYMBAL_1, CRASH_CYMBAL_2, CHINESE_CYMBAL, SPLASH_CYMBAL],
})


AccentedPercussionMap = PercussionMap({
        # bass drum 
        0: [(ACCOUSTIC_BASS_DRUM, 0), (BASS_DRUM_1, 0)],
        # snare
        2: [(SIDE_STICK, 0), (ACCOUSTIC_SNARE, 0), (HAND_CLAP, 0), (ELECTRIC_SNARE, 0)], 
        # toms
        4: [(LOW_FLOOR_TOM, 0), (HIGH_FLOOR_TOM, 0.17), (LOW_TOM, 0.33), (LOW_MID_TOM, 0.5), (HI_MID_TOM, 0.67), (HIGH_TOM, 1)],
        # hi-hat
        6: [(CLOSED_HI_HAT, 0), (PEDAL_HI_HAT, 0), (OPEN_HI_HAT, 1)],
        # cymbals
        8: [(RIDE_CYMBAL_1, 0), (RIDE_CYMBAL_2, 0), (RIDE_BELL, 0), (TAMBOURINE, 0), (COWBELL, 0), (CRASH_CYMBAL_1, 1), (CRASH_CYMBAL_2, 1), (CHINESE_CYMBAL, 1), (SPLASH_CYMBAL, 1)]
})