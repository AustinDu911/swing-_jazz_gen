import mido
import os
import re

# Constants
NOTE_ON = 'note_on'
NOTE_OFF = 'note_off'
REST_SYMBOL = -1  # Define rest as -1 for state representation

# Note-to-Number Mapping (C = 0, C# = 1, ..., B = 11)
NOTE_TO_NUMBER = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7,
                  'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}

# Keys and their transposition offsets to C Major / A Minor
KEY_TRANSPOSE_MAP = {
    'C Major': 0, 'A Minor': 0,
    'C# Major': -1, 'Db Major': -1, 'A# Minor': -1, 'Bb Minor': -1,
    'D Major': -2, 'B Minor': -2,
    'D# Major': -3, 'Eb Major': -3, 'C Minor': -3,
    'E Major': -4, 'C# Minor': -4, 'Db Minor': -4,
    'F Major': -5, 'D Minor': -5,
    'F# Major': -6, 'Gb Major': -6, 'D# Minor': -6, 'Eb Minor': -6,
    'G Major': -7, 'E Minor': -7,
    'G# Major': -8, 'Ab Major': -8, 'F Minor': -8,
    'A Major': -9, 'F# Minor': -9, 'Gb Minor': -9,
    'B Major': -11, 'G# Minor': -11, 'Ab Minor': -11
}

def extract_key_from_filename(filename):
    """Extracts the musical key from a filename.

    Args:
        filename (str): The MIDI filename.

    Returns:
        str: The extracted key (e.g., 'Bb Major', 'C Minor'), or None if not found.
    """
    match = re.search(r'_([A-G]#?|Bb|Db|Eb|Gb|Ab)_(major|minor)\.mid$', filename, re.IGNORECASE)
    if match:
        return match.group(1).upper() + " " + match.group(2).capitalize()  # Normalize format
    return None  # Default case if no key is found

def load_midi(file_path):
    """Loads a MIDI file using mido.

    Args:
        file_path (str): The path to the MIDI file.

    Returns:
        mido.MidiFile: A mido MIDI file object.
    """
    try:
        return mido.MidiFile(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: MIDI file not found at {file_path}")
    except Exception as e:
        raise Exception(f"Error opening or reading MIDI file: {e}")

def parse_midi(midi_file, filename, quantization='16th_triplet'):
    """Parses a MIDI file and extracts note data with tempo-relative durations.

    Args:
        midi_file (mido.MidiFile): The MIDI file object.
        filename (str): The MIDI file name (to extract the key).
        quantization (str): The quantization level ('16th_triplet' or other).

    Returns:
        list: A list of note dictionaries with 'note', 'start_time', 'end_time', 'duration'.
    """
    key = extract_key_from_filename(filename)
    if key is None:
        raise ValueError(f"Key not found in filename: {filename}")

    transpose_amount = KEY_TRANSPOSE_MAP.get(key, 0)  # Default to 0 if key is unknown
    notes = []
    tempo = 120  # Default tempo
    note_on_times = {}
    last_note_off_time = 0

    # Detect tempo from MIDI file
    for track in midi_file.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = mido.tempo2bpm(msg.tempo)
                break

    time_scale = 60 / (tempo * midi_file.ticks_per_beat)  # Convert ticks to seconds

    for track in midi_file.tracks:
        for msg in track:
            current_time = msg.time * time_scale
            if msg.type == 'note_on' and msg.velocity > 0:
                rest_duration = current_time - last_note_off_time
                if rest_duration > (60 / tempo / 4):  # Threshold: 16th note
                    notes.append({'note': REST_SYMBOL, 'start_time': last_note_off_time, 'end_time': current_time,
                                  'duration': quantize_duration(rest_duration, tempo)})

                note_number = (msg.note + transpose_amount) % 12  # Transpose note
                note_on_times[note_number] = current_time

            elif msg.type in ['note_off', 'note_on'] and msg.velocity == 0:
                note_number = (msg.note + transpose_amount) % 12  # Transpose note
                if note_number in note_on_times:
                    start_time = note_on_times[note_number]
                    duration = current_time - start_time
                    notes.append({'note': note_number, 'start_time': start_time, 'end_time': current_time,
                                  'duration': quantize_duration(duration, tempo)})
                    last_note_off_time = current_time
                    del note_on_times[note_number]

    return notes

def quantize_duration(duration, tempo):
    """Quantizes a duration to the closest 16th note or triplet.

    Args:
        duration (float): The duration in seconds.
        tempo (int): The tempo in BPM.

    Returns:
        float: The quantized duration in beats.
    """
    beat_length = 60 / tempo  # Duration of one beat in seconds
    duration_beats = duration / beat_length  # Convert to beats

    sixteenth_notes = duration_beats * 4
    sixteenth_triplets = duration_beats * 6

    if abs(round(sixteenth_notes) - sixteenth_notes) < abs(round(sixteenth_triplets) - sixteenth_triplets):
        return round(sixteenth_notes) / 4
    return round(sixteenth_triplets) / 6

def create_states(parsed_data):
    """Creates a list of unique states from parsed MIDI data.

    Args:
        parsed_data (list): A list of dictionaries, where each dictionary represents a note
                             and contains 'note', 'start_time', and 'end_time'.

    Returns:
        list: A list of unique states (e.g., just note values).
    """

    states = set()  # Using a set to ensure unique states
    for note_data in parsed_data:
        states.add((note_data['note'], note_data['duration']))  # add the tuple (note, duration) to the set
    return list(states)  # Convert back to a list before returning

def create_midi_file(notes, filename="output.mid", tempo=120):
    """Creates a MIDI file from a sequence of notes.

    Args:
        notes (list): A list of (note, duration) tuples.
        filename (str): The output filename.
        tempo (int): The tempo in BPM.
    """
    midi_dir = "midi_creations"
    os.makedirs(midi_dir, exist_ok=True)
    file_path = os.path.join(midi_dir, filename)

    midi_file = mido.MidiFile()
    track = mido.MidiTrack()
    midi_file.tracks.append(track)
    track.append(mido.Message('set_tempo', tempo=mido.bpm2tempo(tempo), time=0))

    for note in notes:
        if note[0] == REST_SYMBOL:
            continue
        track.append(mido.Message('note_on', note=note[0], velocity=100, time=0))
        track.append(mido.Message('note_off', note=note[0], velocity=100, time=int(note[1] * midi_file.ticks_per_beat)))

    midi_file.save(file_path)
    print(f"MIDI file saved to {file_path}")