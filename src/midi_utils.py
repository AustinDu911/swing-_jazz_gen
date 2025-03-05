# midi_utils.py
import mido
import os

# Constants (for readability and maintainability)
NOTE_ON = 'note_on'
NOTE_OFF = 'note_off'
SET_TEMPO = 'set_tempo'
REST_SYMBOL = -1 #define rest as negative 1

def load_midi(file_path):
    """Loads a MIDI file using mido.

    Args:
        file_path (str): The path to the MIDI file.

    Returns:
        mido.MidiFile: A mido MIDI file object.

    Raises:
        FileNotFoundError: If the MIDI file is not found.
        Exception: If the file cannot be opened or read.
    """
    try:
        midi_file = mido.MidiFile(file_path)
        return midi_file
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: MIDI file not found at {file_path}")
    except Exception as e:
        raise Exception(f"Error opening or reading MIDI file: {e}")

def parse_midi(midi_file, quantization='16th_triplet'):
    """Parses a mido MIDI file object to extract note information and quantize durations.

    Args:
        midi_file (mido.MidiFile): The MIDI file object.
        quantization (str): The quantization level ('16th_triplet' or other).

    Returns:
        list: A list of dictionaries, where each dictionary represents a note
              and contains 'note', 'start_time', 'end_time', and 'duration' (quantized).
    """
    notes = []
    tempo = 120  # Default tempo (BPM). Can be overridden by MIDI file messages.
    time_scale = 60 / (tempo * midi_file.ticks_per_beat) #Scale midi ticks to seconds
    current_time = 0  # Current time in seconds
    note_on_messages = {} # Dictionary to store note on times for each note value.
    last_note_off_time = 0 #keep track of the last note off time
    
    # Get tempo from midi file, the mido way
    for track in midi_file.tracks:
        for message in track:
            if message.type == 'set_tempo':
                tempo = mido.tempo2bpm(message.tempo)
                break
    
    time_scale = 60 / (tempo * midi_file.ticks_per_beat) #recalculate time_scale


    for track in midi_file.tracks: #Iterate through tracks in the midi file.
        for message in track: #iterate through messages in the track
            current_time += message.time * time_scale #increment current time to the message time
            if message.type == SET_TEMPO: #Override default tempo if the file contains the value
                tempo = mido.tempo2bpm(message.tempo)
                time_scale = 60 / (tempo * midi_file.ticks_per_beat) #recalculate time_scale
            elif message.type == NOTE_ON: #if a note has started
                
                #Before processing the note on, check if there is a rest.
                rest_duration = current_time - last_note_off_time
                if rest_duration > (60 / tempo / 4):  # Threshold: 16th note, to define a rest
                    # Quantize the rest duration
                    beat_length = 60 / tempo  # Length of one beat in seconds
                    duration_beats = rest_duration / beat_length  # Duration in beats

                    # Quantize to 16th notes and 16th note triplets
                    sixteenth_notes = duration_beats * 4
                    sixteenth_triplets = duration_beats * 6

                    # Calculate the distance to the nearest 16th note and 16th note triplet
                    sixteenth_note_distance = abs(round(sixteenth_notes) - sixteenth_notes)
                    sixteenth_triplet_distance = abs(round(sixteenth_triplets) - sixteenth_triplets)

                    if sixteenth_note_distance < sixteenth_triplet_distance:
                        quantized_duration = round(sixteenth_notes) / 4  # Convert back to beats
                    else:
                        quantized_duration = round(sixteenth_triplets) / 6 # Convert back to beats

                    notes.append({
                        'note': REST_SYMBOL,  # Use -1 to indicate a rest
                        'start_time': last_note_off_time,
                        'end_time': current_time,
                        'duration': quantized_duration
                    })
                if message.velocity > 0: #A note on event is only registered if velocity is greater than 0.
                    note_on_messages[message.note] = current_time #set note on messages in the dictionary
                else: #velocity == 0 is equivalent to note_off
                    if message.note in note_on_messages: #If note is in dictionary then we can create a note
                        start_time = note_on_messages[message.note] #get the start time from note_on_messages
                        end_time = current_time #set the end time to current_time
                        duration = end_time - start_time #calculate the duration by taking the difference

                        # Quantization logic starts here
                        beat_length = 60 / tempo  # Length of one beat in seconds
                        duration_beats = duration / beat_length  # Duration in beats

                        # Quantize to 16th notes and 16th note triplets
                        sixteenth_notes = duration_beats * 4
                        sixteenth_triplets = duration_beats * 6

                        # Calculate the distance to the nearest 16th note and 16th note triplet
                        sixteenth_note_distance = abs(round(sixteenth_notes) - sixteenth_notes)
                        sixteenth_triplet_distance = abs(round(sixteenth_triplets) - sixteenth_triplets)

                        if sixteenth_note_distance < sixteenth_triplet_distance:
                            quantized_duration = round(sixteenth_notes) / 4  # Convert back to beats
                        else:
                            quantized_duration = round(sixteenth_triplets) / 6 # Convert back to beats

                        notes.append({ #Append a dictionary of note info to the notes list.
                            'note': message.note,
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration': quantized_duration #store the calculated quantized duration
                        })
                        del note_on_messages[message.note] #remove the note from note_on_messages dictionary
            elif message.type == NOTE_OFF: #if a note is ending
                if message.note in note_on_messages: #if note is in dictionary then we can create a note
                    start_time = note_on_messages[message.note] #get the start time from note_on_messages
                    end_time = current_time #set the end time to current_time
                    duration = end_time - start_time #calculate the duration by taking the difference
                    last_note_off_time = current_time #update the last note off time

                    # Quantization logic starts here
                    beat_length = 60 / tempo  # Length of one beat in seconds
                    duration_beats = duration / beat_length  # Duration in beats

                    # Quantize to 16th notes and 16th note triplets
                    sixteenth_notes = duration_beats * 4
                    sixteenth_triplets = duration_beats * 6

                    # Calculate the distance to the nearest 16th note and 16th note triplet
                    sixteenth_note_distance = abs(round(sixteenth_notes) - sixteenth_notes)
                    sixteenth_triplet_distance = abs(round(sixteenth_triplets) - sixteenth_triplets)

                    if sixteenth_note_distance < sixteenth_triplet_distance:
                        quantized_duration = round(sixteenth_notes) / 4  # Convert back to beats
                    else:
                        quantized_duration = round(sixteenth_triplets) / 6 # Convert back to beats


                    notes.append({ #Append a dictionary of note info to the notes list.
                        'note': message.note,
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': quantized_duration #store the calculated duration
                    })
                    del note_on_messages[message.note] #remove the note from note_on_messages dictionary

    return notes

def create_states(parsed_data):
    """Creates a list of unique states from parsed MIDI data.

    Args:
        parsed_data (list): A list of dictionaries, where each dictionary represents a note
                             and contains 'note', 'start_time', and 'end_time'.

    Returns:
        list: A list of unique states (e.g., just note values).
    """

    states = []
    for note_data in parsed_data:
        states.append( (note_data['note'], note_data['duration']) ) #create a tuple from the note and duration.
    return states

def create_midi_file(notes, filename="output.mid", tempo=120):
    """
    Creates a MIDI file from a list of notes.
    """
    midi_dir = "midi_creations"  # Name of the output directory

    # Create the output directory if it doesn't exist
    if not os.path.exists(midi_dir):
        os.makedirs(midi_dir)

    file_path = os.path.join(midi_dir, filename) #set the midi path

    # Create midi file
    midi_file = mido.MidiFile()
    track = mido.MidiTrack()
    midi_file.tracks.append(track)

    # Set tempo
    track.append(mido.Message('set_tempo', tempo=mido.bpm2tempo(tempo), time=0))

    track.append(mido.Message('program_change', program=0, time=0)) #Program change to piano
    current_time = 0 #start at zero, to get timing
    ticks_per_beat = midi_file.ticks_per_beat

    for note in notes:
        midi_note = note[0]
        duration = note[1]

        if midi_note == REST_SYMBOL: #it is a rest, so continue
            continue

        # Convert quantized duration to MIDI ticks
        if duration % (1/3) == 0: # Check if its an triplet
            ticks = int((duration / (1/3)) * (ticks_per_beat / 3))
        else:
            ticks = int(duration * ticks_per_beat)
        track.append(mido.Message('note_on', note=midi_note, velocity=100, time = 0)) #add note with velocity
        track.append(mido.Message('note_off', note=midi_note, velocity=100, time=ticks)) #remove note

    midi_file.save(file_path)
    print(f"Midi file saved to {file_path}")
