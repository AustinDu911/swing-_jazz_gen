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
    match = re.search(r'_([A-G]#?|Bb|Db|Eb|Gb|Ab)_(major|minor)\.mid$', filename, re.IGNORECASE)
    if match:
        key_note = match.group(1)  # Keep original formatting
        key_type = match.group(2)  # Keep original "major"/"minor" case

        # Debugging print
        print(f"Extracted key: {key_note} {key_type} from {filename}")

        # Ensure Bb is correctly formatted (prevent "BB" issue)
        if key_note.upper() == "BB":
            key_note = "Bb"

        extracted_key = f"{key_note} {key_type}"
        print(f"Formatted key: {extracted_key}")

        return extracted_key  # Maintain original capitalization for "major"/"minor"
    
    print(f"Key not found in filename: {filename}")  # Debugging message if key extraction fails
    return None
    
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
    key = extract_key_from_filename(filename)
    if key is None:
        raise ValueError(f"Key not found in filename: {filename}")

    transpose_amount = KEY_TRANSPOSE_MAP.get(key, 0)
    notes = []
    tempo = 500000  # Default tempo in microseconds per beat
    note_on_times = {}
    last_note_off_time = 0

    found_tempo = False
    for track in midi_file.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                found_tempo = True
                break  # Stop searching once tempo is found

    if not found_tempo:
        print(f"⚠️ Warning: No 'set_tempo' message found in {filename}. Using default 120 BPM.")
        tempo = 500000  # Default to 120 BPM

    time_scale = 60 / (mido.tempo2bpm(tempo) * midi_file.ticks_per_beat)

    for track in midi_file.tracks:
        for msg in track:
            current_time = msg.time * time_scale

            if msg.type == 'note_on' and msg.velocity > 0:
                rest_duration = current_time - last_note_off_time
                if rest_duration > (60 / mido.tempo2bpm(tempo) / 4):  
                    notes.append({
                        'note': REST_SYMBOL,
                        'start_time': last_note_off_time,
                        'end_time': current_time,
                        'duration': quantize_duration(rest_duration, mido.tempo2bpm(tempo))
                    })

                note_number = (msg.note + transpose_amount) % 12
                note_on_times[note_number] = current_time

            elif msg.type in ['note_off', 'note_on'] and msg.velocity == 0:
                note_number = (msg.note + transpose_amount) % 12
                if note_number in note_on_times:
                    start_time = note_on_times[note_number]
                    duration = current_time - start_time
                    notes.append({
                        'note': note_number,
                        'start_time': start_time,
                        'end_time': current_time,
                        'duration': quantize_duration(duration, mido.tempo2bpm(tempo))
                    })
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

# Additional

def transpose_to_key(sequence, key):
    """
    Transposes a sequence of notes to the specified key.
    
    Args:
        sequence (list): A list of tuples (note, duration).
        key (str): The target key (e.g., "C major", "A minor").
    
    Returns:
        list: A transposed list of tuples (note, duration).
    """
    key_base = key.split()[0]  # Extract the note (e.g., "Bb" from "Bb major")
    if key_base not in NOTE_TO_NUMBER:
        raise ValueError(f"Invalid key: {key}. Must be one of {', '.join(NOTE_TO_NUMBER.keys())}")

    transpose_amount = NOTE_TO_NUMBER[key_base]  # Get shift from C major

    transposed_sequence = []
    for note, duration in sequence:
        if note == REST_SYMBOL:
            transposed_note = REST_SYMBOL  # Keep rests unchanged
        else:
            transposed_note = (note + transpose_amount) % 12  # Keep within 0-11 range
        
        transposed_sequence.append((transposed_note, duration))
    
    return transposed_sequence



def convert_midi_to_states(midi_file):
    """
    Converts a MIDI file to a list of states (note, duration).
    
    Args:
        midi_file (str): The path to the MIDI file.
    
    Returns:
        list: A list of tuples, where each tuple is (note, duration).
    """
    states = []
    midi = mido.MidiFile(midi_file)
    tempo = 500000  # Default tempo (in microseconds per beat)
    
    for track in midi.tracks:
        time = 0
        for msg in track:
            time += msg.time
            if msg.type == 'set_tempo':
                tempo = msg.tempo  # Update tempo if found
            if msg.type == 'note_on' and msg.velocity > 0:
                note = msg.note
                duration = (time / midi.ticks_per_beat) * (tempo / 1000000.0)  # Convert ticks to seconds
                states.append((note, duration))
    
    return states

def get_midi_files_in_directory(directory):
    """
    Returns a list of paths to all MIDI files in the specified directory.
    
    Args:
        directory (str): The path to the directory containing MIDI files.
    
    Returns:
        list: A list of file paths to the MIDI files in the directory.
    """
    if not os.path.exists(directory):
        print(f"Warning: Directory '{directory}' does not exist.")
        return []  # Return empty list instead of crashing
    
    midi_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(('.mid', '.midi'))]
    return midi_files