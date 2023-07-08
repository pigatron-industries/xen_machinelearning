


class PercussionMap:
    """A map of percussion instruments to MIDI note numbers."""

    # Default percussion map
    map = {
        1: [35, 36],                     # Bass Drum: Acoustic Bass Drum, Bass Drum 1 
        2: [38, 39, 40],                 # Snare: Acoustic Snare, Hand Clap, Electric Snare
        3: [41, 43, 45, 47, 48, 50],     # Toms: Low Floor Tom, High Floor Tom, Low Tom, Low-Mid Tom, Hi-Mid Tom, High Tom
        4: [42, 44],                     # Closed Hi-Hat: Closed Hi-Hat, Pedal Hi-Hat
        5: [46, 51],                     # Open Hi-Hat: Open Hi-Hat, Crash Cymbal 1, Ride Cymbal 1
        6: [49, 52, 53, 54, 55, 56, 57, 59], # Cymbals: Chinese Cymbal, Ride Bell, Tambourine, Splash Cymbal, Cowbell, Crash Cymbal 2, Ride Cymbal 2
    }

    def __call__(self, midi):
        """Get the instrument group number for the given midi note number."""
        for group, notes in self.map.items():
            if midi in notes:
                return group
        return 0