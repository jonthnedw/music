from typing import List
from instrument import Instrument

import music21

# Class creates a song object from a midi file  
class Song:
    def __init__(self, path: str=None) -> None:
        self.name: str = None
        self.parts: List[Instrument] = None
        self.time_signature = None

        try:
            stream = music21.converter.parse(path) 
            parts = stream.parts.stream()
            
            self.time_signature = (stream.flat.timeSignature.numerator, stream.flat.timeSignature.denominator)
            self.name = path[(-(path[::-1].find("/"))):-4]
            print(f"Loading Song: {self.name} with {len(parts)} parts.")
            
            self.parts = [Instrument(part, self.time_signature) for part in parts]
        except Exception as e:
            print(f"Failed to load song with path: {path}, exception: {e}.")
    
    def write_to_file(self, path: str) -> None:
        score = music21.stream.Score()
        score.timeSignature = music21.meter.TimeSignature(f"{self.time_signature[0]}/{self.time_signature[1]}")
        path = path or (self.name + ".mid") 

        for i, part in enumerate(self.parts):
            score.insert(i, part.music21())

        file = music21.midi.translate.streamToMidiFile(score)
        file.open(path, 'wb')
        file.write()
        file.close()