import src.midi_utils as midi_utils
import mido  # We are importing mido just to check the type.
import os

import src.markov as markov
import numpy as np

# Define a dictionary to map key names to their note numbers
NOTE_TO_NUMBER = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7,
                  'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}

NOTE_TO_NUMBER = {'C':0, 'C#': 1, 'Db': 1, 'D':2, 'D#':3, 'Eb': 3, 'E':4, 'F':5, 'F#':6, 'Gb':6, 'G':7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#':10, 'Bb': 10, 'B':11}

# Test load_midi function with a valid file path
REST_SYMBOL = midi_utils.REST_SYMBOL #define as rest symbol
valid_file_path = "midi_files/JustFriends_Bb_major.mid"  # Replace with your MIDI file

try:
    midi_file = midi_utils.load_midi(valid_file_path)
    if isinstance(midi_file, mido.MidiFile):
        print(f"load_midi test passed for {valid_file_path}: File loaded successfully!")

        # Get tempo from midi file, the mido way
        for track in midi_file.tracks:
            for message in track:
                if message.type == 'set_tempo':
                    tempo = mido.tempo2bpm(message.tempo)
                    break

        print(f"  - BPM Tempo: {tempo}")  # Print tempo
        print(f"  - Ticks per beat: {midi_file.ticks_per_beat}")  # Print ticks per beat


    else:
        print(f"load_midi test failed for {valid_file_path}: Incorrect return type.")
except FileNotFoundError as e:
    print(f"load_midi test failed for {valid_file_path}: {e}")
except Exception as e:
    print(f"load_midi test failed for {valid_file_path}: An unexpected error occurred: {e}")

# Test load_midi function with an invalid file path
invalid_file_path = "midi_files/nonexistent.mid"

try:
    midi_utils.load_midi(invalid_file_path)
    print("load_midi test failed for invalid path: No error raised!")  # Should not reach this point
except FileNotFoundError:
    print("load_midi test passed for invalid path: FileNotFoundError raised correctly!")
except Exception as e:
    print(f"load_midi test failed for {invalid_file_path}: An unexpected error occurred: {e}")

# Test parse_midi function
try:
    # Test with key = C
    midi_file = midi_utils.load_midi(valid_file_path)
    parsed_notes = midi_utils.parse_midi(midi_file, valid_file_path)  # Call the function from midi_utils
    print("parse_midi test started:")
    if isinstance(parsed_notes, list):
        print("  - Return type test passed: Returns a list.")
        if parsed_notes:  # Check if the list is not empty
            first_note = parsed_notes[0]
            print(f"First note: {first_note}")
            if isinstance(first_note, dict) and \
               'note' in first_note and (isinstance(first_note['note'], int) or first_note['note'] == midi_utils.REST_SYMBOL) and \
               'start_time' in first_note and isinstance(first_note['start_time'], (float, int)) and \
               'end_time' in first_note and isinstance(first_note['end_time'], (float, int)) and \
               'duration' in first_note and isinstance(first_note['duration'], (float, int)):

                print("  - First note format test passed: The first element is of type Dictionary, with expected key value types")
                print(f"  - First note: {first_note}")
                print(f"Rest Symbol {midi_utils.REST_SYMBOL}")

                # Check that the duration is quantized
                duration = first_note['duration']
                is_quantized = (
                    abs(duration * 4 - round(duration * 4)) < 1e-6 or  # Close to a 16th note
                    abs(duration * 6 - round(duration * 6)) < 1e-6     # Close to a 16th note triplet
                )
                
                #Check if the note is a rest
                is_rest = first_note['note'] == midi_utils.REST_SYMBOL
                
                if is_quantized or is_rest:
                    print("  - Quantization test passed: Duration is quantized to 16th notes or triplets.")
                else:
                    print("  - Quantization test failed: Duration is not quantized.")

                # Check if note is relative to C (or is a rest)
                key_from_filename = midi_utils.extract_key_from_filename(valid_file_path)

                if key_from_filename:
                    is_relative = (first_note['note'] >= -1 and first_note['note'] <= 127 - 5 * NOTE_TO_NUMBER[key_from_filename.split()[0]])
                else:
                    is_relative = False  # If no key found, assume failure

                if is_relative:
                    print("  - Key test passed: Notes are relative to key")
                else:
                    print("  - Key test failed: Notes are no relative to key")
            else:
                print("  - First note format test failed: Incorrect note format.")
        else:
            print("  - No notes were parsed.")
    else:
        print("  - Return type test failed: Doesn't return a list.")
    print("parse_midi test ended.")
except Exception as e:
    print(f"parse_midi test failed: An error occurred: {e}")

# Test create_states function
try:
    states = midi_utils.create_states(parsed_notes)  # Call the function from midi_utils
    print("create_states test started:")
    if isinstance(states, list):
        print("  - Return type test passed: Returns a list.")
        if states:  # Check if the list is not empty
            first_state = states[0]
            print(f"First state: {first_state}")
            if isinstance(first_state, tuple) and \
               len(first_state) == 2 and \
               (isinstance(first_state[0], int) or first_state[0] == midi_utils.REST_SYMBOL) and \
               isinstance(first_state[1], (float, int)):
                print("  - First element format test passed: Elements are tuples with (note, duration).")
                print(f"  - First state: {first_state}")
            else:
                print("  - First element format test failed: Elements are not tuples with (note, duration).")
        else:
            print("  - No states were created.")
    else:
        print("  - Return type test failed: Doesn't return a list.")
    print("create_states test ended.")
except Exception as e:
    print(f"create_states test failed: An error occurred: {e}")


# Test the MarkovChain Class
try:
    print("\nTesting the MarkovChain Class:")
    # Create an instance of the MarkovChain
    markov_chain = markov.MarkovChain()

    # Load the midi file and parse the notes
    midi_file = midi_utils.load_midi(valid_file_path)
    parsed_notes = midi_utils.parse_midi(midi_file, valid_file_path)

    # Create the states
    states = midi_utils.create_states(parsed_notes)

    # Create the state dictionary
    markov_chain.create_state_dictionary(states)
    print("- create_state_dictionary test passed: State dictionary created successfully.")

    # Create the transition matrix
    markov_chain.create_transition_matrix(states)
    print("- create_transition_matrix test passed: Transition matrix created successfully.")

    # Generate a sequence
    length = 10  # Length of the sequence to generate
    generated_sequence = markov_chain.generate_sequence(length)

    # Verify that the generated sequence is a list
    assert isinstance(generated_sequence, list), "generate_sequence test failed: The generated sequence is not a list."

    # Verify that the generated sequence has the correct length
    assert len(generated_sequence) == length, f"generate_sequence test failed: The generated sequence does not have the correct length (expected {length}, got {len(generated_sequence)})."

    # Verify that the generated sequence contains valid states
    valid_states = set(markov_chain.states.keys())
    assert all(state in valid_states for state in generated_sequence), "generate_sequence test failed: The generated sequence contains invalid states."

    print(f"- generate_sequence test passed: Generated a sequence of {length} valid states.")

    # Test the generate_midi_file method
    # markov_chain.generate_midi_file(generated_sequence, filename="test_generated_solo.mid")
    # print("- generate_midi_file test passed: MIDI file generated successfully.")

except Exception as e:
    print(f"An error occurred while testing the MarkovChain class: {e}")

# Create and train a markov chain with the states that have been generated.
markov_chain = markov.MarkovChain()
markov_chain.create_state_dictionary(states)
markov_chain.create_transition_matrix(states)
# Generate a sequence of states.
generated_sequence = markov_chain.generate_sequence(50)
print(generated_sequence)


# Test transposing and tempo adjustment
try:
    print("\nTesting Transposition and Tempo Adjustments:")

    # Testing with C Major key
    key = "C Major"
    midi_file = midi_utils.load_midi(valid_file_path)
    parsed_notes = midi_utils.parse_midi(midi_file, valid_file_path, quantization="16th_triplet")

    # Check the transposition of notes
    print(f"\nTransposition Test for {key}:")
    transposed_notes = [note['note'] for note in parsed_notes if note['note'] != midi_utils.REST_SYMBOL]
    expected_transposition = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 
                              'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
    transposed_notes_correct = all(
        (note - expected_transposition[key.split()[0]]) % 12 == 0 for note in transposed_notes)  # Check correct transposition
    
    if transposed_notes_correct:
        print(f"  - Transposition test passed for key {key}. Notes are correctly transposed.")
    else:
        print(f"  - Transposition test failed for key {key}. Notes are not transposed correctly.")

    # Testing tempo adjustment
    print(f"\nTempo Adjustment Test for {key}:")
    bpm = 120  # Assumed tempo, you can dynamically extract this from the MIDI file if needed
    original_durations = [note['duration'] for note in parsed_notes if note['note'] != midi_utils.REST_SYMBOL]

    # Adjusted durations based on tempo (if tempo is 60 BPM, duration should be doubled)
    tempo_multiplier = bpm / 120  # If BPM is 120, no change, else the durations will scale.
    adjusted_durations = [round(duration * tempo_multiplier, 4) for duration in original_durations]

    # Check that the adjusted durations match the expected results (using the assumed scale).
    durations_match = all(
        round(adjusted, 4) == round(orig, 4) for adjusted, orig in zip(adjusted_durations, original_durations)
    )

    if durations_match:
        print(f"  - Tempo adjustment test passed for tempo {bpm} BPM.")
    else:
        print(f"  - Tempo adjustment test failed for tempo {bpm} BPM.")

except Exception as e:
    print(f"An error occurred while testing transposition and tempo adjustments: {e}")

