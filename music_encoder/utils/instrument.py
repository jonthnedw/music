from typing import List, Union
from music21.stream import Measure
from music21.note import Note as m21Note
from music21.chord import Chord as m21Chord
from music21.stream import Part
from music21.duration import Duration
from music21.meter import TimeSignature


# Note class to store note information
class Note:
    # Class function for creating note objects from string
    def from_string(str_repr: str):
        # TODO: Add validation check
        ls_repr = str_repr.split("|")[1:-1]

        is_chord = "," in ls_repr[0]
        name = name.split(",") if is_chord else ls_repr[0]
        duration = [float(d) for d in duration.split(",")] if is_chord else ls_repr[1]
        offset = ls_repr[2]
        velocity = [float(v) for v in velocity.split(",")] if is_chord else ls_repr[3]
        measure = ls_repr[4]

        return Note(name, duration, offset, velocity, measure)


    def __init__(self, name, duration, offset, velocity, measure) -> None:
        self.name: Union[str, List[str]] = name
        self.duration: Union[float, List[float]] = duration
        self.offset: float = offset
        self.velocity: Union[float, List[float]] = velocity
        self.measure: int = measure

        self.is_chord: bool = type(name) is not str

    # String representation for NLP model
    def __str__(self) -> str:
        name = ",".join(self.name) if self.is_chord else self.name
        duration = ",".join([str(d) for d in self.duration]) if self.is_chord else self.duration
        velocity = ",".join([str(v) for v in self.velocity]) if self.is_chord else self.velocity

        return f"|{name}|{duration}|{self.offset}|{velocity}|{self.measure}|"


    def music21(self) -> Union[m21Note, m21Chord]:
        data = None
        if self.is_chord:
            chord_notes = []
            for i in range(len(self.name)):
                note = m21Note(self.name[i])
                note.duration = Duration(self.duration[i])
                note.offset = self.offset
                note.volume.velocity = self.velocity[i]
                chord_notes.append(note)
            data = m21Chord(chord_notes)
        else:
            data = m21Note(self.name)
            data.duration = Duration(self.duration)
            data.offset = self.offset
            data.volume.velocity = self.velocity
        return data


# Instrument containing a sequence of notes and chords
class Instrument:
    def __init__(self, note_data: Part = None, time_signature = None) -> None:
        self.notes: List[Note] = []
        self.time_signature = time_signature
        
        measure_counter = 0
        for measure in note_data.getElementsByClass(Measure):
            for note in measure.flat.notes: 
                if isinstance(note, m21Note):
                    self.notes.append(Note(note.pitch.nameWithOctave, note.duration.quarterLength, note.offset, note.volume.velocity, measure_counter))
                if isinstance(note, m21Chord):
                    names = [n.nameWithOctave for n in note.pitches]
                    durations = [n.duration.quarterLength for n in note]
                    offset = note.offset
                    velocities = [n.volume.velocity for n in note]
                    self.notes.append(Note(names, durations, offset, velocities, measure_counter))
            measure_counter += 1
        #self._consolidate_notes()

    def music21(self) -> Part:
        part = Part(id="Piano")

        i = 0
        while i < len(self.notes):
            j = i
            measure = Measure(timeSignature=TimeSignature(f"{self.time_signature[0]}/{self.time_signature[1]}"))
            while j < len(self.notes) and self.notes[i].measure == self.notes[j].measure:
                measure.insert(self.notes[j].offset % self.time_signature[0], self.notes[j].music21())
                j += 1
            part.append(measure)
            i = j 

        return part

    def __str__(self) -> str:
        return " ".join([str(note) for note in self.notes])

