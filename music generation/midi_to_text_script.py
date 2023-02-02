from augmentation import augment, jitter, octave_up, octave_down, invert_chord

from sys import argv
from os import listdir
from song import Song


def main():
    midi_dir = argv[1]
    text_dir = argv[2]

    midi_files = listdir(midi_dir)
    for file_name in midi_files:
        s = Song(midi_dir + "/" + file_name)
        if s.parsed:
            s.to_text(text_dir + "/" + s.name + ".txt")

            # Include augmentation
            augment(s, jitter).to_text(text_dir + "/" + s.name + "_jitter.txt")
            augment(s, octave_up).to_text(text_dir + "/" + s.name + "_oct_up.txt")
            augment(s, octave_down).to_text(text_dir + "/" + s.name + "_oct_down.txt")
            augment(s, invert_chord, True).to_text(text_dir + "/" + s.name + "_invert_chord.txt")

            # all augments
            augment(augment(augment(s, jitter), octave_down), invert_chord, True).to_text(text_dir + "/" + s.name + "_aug.txt")



if __name__ == "__main__":
    main()