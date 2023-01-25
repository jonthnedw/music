from fractions import Fraction

from typing import List, Union
from music21.stream import Measure as m21Measure
from music21.note import Note as m21Note
from music21.chord import Chord as m21Chord
from music21.stream import Part as m21Part
from music21.meter import TimeSignature
from music21.converter import parse as m21parse
from music21.stream import Score
from music21.midi.translate import streamToMidiFile


NOTES = ["A" , "B", "C", "D", "E", "F", "G"]
ACC = ["#", "-"]


def note_to_num(s: str) -> str:
    "Convert a note string into a string of an int. Example: 'G#3' -> '713'"

    if not (2 <= len(s) <= 3):
        raise Exception(f"Note string: {s} is wrong length")
    return_s = ""
    return_s += str(NOTES.index(s[0]) + 1)
    return_s += "" if len(s) == 2 else str(ACC.index(s[1]) + 1)
    return_s += s[-1]
    return return_s

def num_to_note(s: str) -> str:
    "Convert an int string into a note string. Example: '622' -> 'F-2'"

    if not (2 <= len(s) <= 3):
        raise Exception(f"Number string: {s} is wrong length")
    return_s = ""
    return_s += NOTES[int(s[0]) - 1]
    return_s += "" if len(s) == 2 else ACC[int(s[1]) - 1]
    return_s += s[-1]
    return return_s


def decimal_shift(f: float) -> str:
    "Shift a float until it is a integer. Example: 12.34 -> '2 1234'"
    shift = 0
    while not f.is_integer():
        f  *= 10
        f = round(f, 3)
        shift += 1
    return f"{shift} {int(f)}"

def reverse_decimal_shift(shift: str, num: str) -> float:
    "Revert a decimal shift string back to a float. Example: '1 15' -> 1.5"

    shift = int(shift)
    num = float(num)
    while shift > 0:
        num /= 10
        shift -= 1
    return num

def string_to_time_signature(s: str) -> tuple:
    return tuple(s.split("/"))

def time_signature_to_string(t: tuple) -> str:
    return f"{t[0]}/{t[1]}"


class Note:
    """
    The representation of a note is a sequence of numbers. For the model to 
    learn music generation, each note is represented as a sequence of 4 components:
    pitch value, duration, offset in measure, velocity. 

    For duration and offset an int preceding those values indicates the number
    of decimal places to shift since these values are floats:
        1.25 2 -> 2 125 0 2

    A full note representation:
        714 1 5 1 25 130 = G#4 half note that is 2.5 quarter notes in the measure 
            with 130 velocity.
    """
    def __init__(self, m21_note: m21Note=None, string_list: List[str]=None) -> None:
        self.name: str = None
        self.duration: float = None
        self.offset: float = None
        self.velocity: int = None
        
        if m21_note:
            self.name = m21_note.pitch.nameWithOctave
            self.duration = float(round(m21_note.quarterLength, 3))
            self.offset = float(round(m21_note.offset, 3))
            self.velocity = int(m21_note.volume.velocity)
        elif string_list:
            if len(string_list) != 6:
                raise Exception(f"Cannot convert string list {string_list} to note.")
            self.name = num_to_note(string_list[0])
            self.duration = reverse_decimal_shift(string_list[1], string_list[2])
            self.offset = reverse_decimal_shift(string_list[3], string_list[4])
            self.velocity = int(string_list[5])
            
    def music21(self) -> m21Note:
        note = m21Note(self.name)
        note.quarterLength = self.duration
        note.offset = self.offset
        note.volume.velocity = self.velocity
        return note

    def partial_string(self, duration=True, offset=True, velocity=True) -> str:
        s = [note_to_num(self.name)]
        if duration:
            s.append(decimal_shift(self.duration))
        if offset:
            s.append(decimal_shift(self.offset))
        if velocity:
            s.append(str(self.velocity))
        return " ".join(s) 

    def tokenize(self):
        return [note_to_num(self.name), decimal_shift(self.duration), decimal_shift(self.offset), str(self.velocity)]

    def __str__(self) -> str:
        return self.partial_string()


class Chord:
    def __init__(self, m21_chord: m21Chord=None, string_list: List[str]=None) -> None:
        self.notes: List[Note] = []
        if m21_chord:
            m21_chord.sortAscending()
            for note in m21_chord:
                note.offset += m21_chord.offset
                self.notes.append(Note(note))
        elif string_list:
            if len(string_list) % 6 != 0:
                raise Exception("String list for chord should be multiple of 6")
            for i in range(int(len(string_list) / 6)):
                self.notes.append(Note(string_list=string_list[i*6:i*6+6]))
        else:
            raise Exception("Object required for chord")
        self.offset = self.notes[0].offset

    def highest_pitch(self) -> Note:
        return self.notes[-1]

    def music21(self) -> m21Chord:
        return m21Chord([n.music21() for n in self.notes])

    def partial_string(self, duration=True, offset=True, velocity=True) -> str:
        s = []
        for note in self.notes:
            s.append(note.partial_string(duration, offset, velocity))
        return " ".join(s) 
    
    def __str__(self) -> str:
        return self.partial_string()


class Measure:
    def __init__(self, time_signature: tuple, offset: Fraction = None, measure_data: m21Measure=None, string_list: List[str]=None) -> None:
        self.time_signature = time_signature
        self.offset = offset 
        self.measure_data: List[Union[Note, Chord]] = []

        if measure_data:
            # Flatten data
            measure_data = measure_data.flatten()
            for data in measure_data:
                if isinstance(data, m21Note):
                    self.measure_data.append(Note(data))
                if isinstance(data, m21Chord):
                    self.measure_data.append(Chord(data))
        elif string_list:
            if len(string_list) % 6 != 0:
                raise Exception("String list for a measure should be multiple of 6.")
            
            i = 0
            while i < len(string_list):
                j = i + 6
                while j < len(string_list) and string_list[i+4] == string_list[j+4]:
                    j += 6
                seq = string_list[i:j]
                data = Note(string_list=seq) if j - i == 6 else Chord(string_list=seq)
                self.measure_data.append(data)
                i = j
    
    def music21(self) -> m21Measure:
        measure = m21Measure(timeSignature=TimeSignature(f"{self.time_signature[0]}/{self.time_signature[1]}"))
        for note_or_chord in self.measure_data:
            offset = note_or_chord.offset
            measure.insert(offset, note_or_chord.music21())
        return measure

    def partial_string(self, duration=True, offset=True, velocity=True) -> str:
        time_signature = f"{self.time_signature[0]}/{self.time_signature[1]}"
        s = [time_signature]
        for note_or_chord in self.measure_data:
            s.append(note_or_chord.partial_string(duration, offset, velocity))
        return " ".join(s)

    def __str__(self) -> str:
        return self.partial_string()

# Instrument containing a sequence of notes and chords
class Instrument:
    def __init__(self, stream: m21Part=None, string_list: List[str]=None) -> None:
        self.measures: List[Measure] = []
        self.num_notes = None

        if stream:
            if len(stream.flat.notes) == 0:
                raise Exception("Instrument stream is empty.")

            self.num_notes = len(stream.flat.notes)

            base_time_signature = (4, 4)
            for measure in stream.getElementsByClass(m21Measure):
                if measure.timeSignature is not None:
                    base_time_signature = (measure.timeSignature.numerator, measure.timeSignature.denominator)
                self.measures.append(Measure(base_time_signature, measure_data=measure))
        elif string_list:
            measure = []
            for i in range(len(string_list)):
                if "/" in string_list[i] and (i != 0 or i == len(string_list) - 1):
                    time_signature = string_to_time_signature(measure[0])
                    self.measures.append(Measure(time_signature, string_list=measure[1:]))
                    measure = []
                measure.append(string_list[i])

    def music21(self) -> m21Part:
        print(self)
        part = m21Part(id=str(len(self.measures)))
        part.append([measure.music21() for measure in self.measures])
        return part

    def partial_string(self, duration=True, offset=True, velocity=True) -> str:
        s = []
        for measure in self.measures:
            s.append(measure.partial_string(duration, offset, velocity))
        return " ".join(s)

    def __str__(self) -> str:
        return self.partial_string()


class Song:
    def __init__(self, path: str=None, parts_as_string_list: List[List[str]]=None, name="Song") -> None:
        self.name: str = None
        self.parts: List[Instrument] = []
        self.num_notes = 0

        if path:
            parts = m21parse(path, forceSource=True, quantizePost=False).parts.stream()
            
            self.name = path[(-(path[::-1].find("/"))):-4]
            self.parts = [Instrument(stream=part) for part in parts]
            self.num_notes = sum([i.num_notes for i in self.parts])
            print(f"Loaded Song: {self.name} with {len(parts)} parts and {self.num_notes} notes.")
        elif parts_as_string_list:
            self.name = name
            for part in parts_as_string_list:
                self.parts.append(Instrument(string_list=part))
            
    
    def write_to_file(self, path: str) -> None:
        score = Score()
        path = path or (self.name + ".mid")

        for i, part in enumerate(self.parts):
            score.insert(i, part.music21())
        file = streamToMidiFile(score)
        file.open(path, 'wb')
        file.write()
        file.close()


s = Song("../examples/ghibli_dataset/Spirited Away - Itsumo Nando Demo (2).mid")
parts = []

for part in s.parts:
    parts.append(str(part).split(" "))
s2 = Song(parts_as_string_list=parts, name="N")
s2.write_to_file("test.mid")
