import sys
import os

# Add the parent directory (swing_jazz_gen/) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from markov import MarkovChain  # ✅ Now Python can find `markov.py`
import midi_utils  # ✅ Now Python can find `midi_utils.py`
import tkinter as tk
from tkinter import messagebox
import numpy as np


class MusicGeneratorApp:
    def __init__(self):
        # Initialize the GUI
        self.window = tk.Tk()
        self.window.title("Music Generator")

        # Key Input
        self.key_label = tk.Label(self.window, text="Key (e.g., C, D, A, Bb):")
        self.key_label.grid(row=0, column=0)
        self.key_entry = tk.Entry(self.window)
        self.key_entry.grid(row=0, column=1)

        # Tempo Input
        self.tempo_label = tk.Label(self.window, text="Tempo (BPM):")
        self.tempo_label.grid(row=1, column=0)
        self.tempo_entry = tk.Entry(self.window)
        self.tempo_entry.grid(row=1, column=1)

        # Major/Minor Selection
        self.scale_label = tk.Label(self.window, text="Scale Type:")
        self.scale_label.grid(row=2, column=0)

        self.scale_var = tk.StringVar()
        self.scale_var.set("major")  # Default to Major

        self.major_button = tk.Radiobutton(self.window, text="Major", variable=self.scale_var, value="major")
        self.major_button.grid(row=2, column=1)
        self.minor_button = tk.Radiobutton(self.window, text="Minor", variable=self.scale_var, value="minor")
        self.minor_button.grid(row=3, column=1)

        # Number of Bars Selection
        self.bars_label = tk.Label(self.window, text="Number of Bars:")
        self.bars_label.grid(row=4, column=0)

        self.bar_var = tk.StringVar()
        self.bar_var.set("32")

        self.bar_32 = tk.Radiobutton(self.window, text="32 Bars", variable=self.bar_var, value="32")
        self.bar_32.grid(row=4, column=1)
        self.bar_64 = tk.Radiobutton(self.window, text="64 Bars", variable=self.bar_var, value="64")
        self.bar_64.grid(row=5, column=1)

        # Generate Button
        self.generate_button = tk.Button(self.window, text="Generate Solo", command=self.on_generate)
        self.generate_button.grid(row=6, columnspan=2)

    def on_generate(self):
        """Handles user input and calls the solo generation method."""
        try:
            tempo = int(self.tempo_entry.get())
            key = self.key_entry.get().strip()
            num_bars = int(self.bar_var.get())
            key_type = self.scale_var.get()  # "major" or "minor"

            # Validate key input
            if key not in midi_utils.NOTE_TO_NUMBER:
                raise ValueError(f"Invalid key. Please enter one of: {', '.join(midi_utils.NOTE_TO_NUMBER.keys())}")

            # Validate tempo input
            if tempo <= 0:
                raise ValueError("Tempo must be a positive integer.")

            # Generate solo
            self.generate_solo(tempo, key, num_bars, key_type)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def generate_solo(self, tempo, key, num_bars, key_type):
        """Generates and saves a Markov Chain-based jazz solo."""

        # Load only major or minor MIDI files
        midi_files = [
            f for f in midi_utils.get_midi_files_in_directory('midi_files')
            if key_type in f.lower()  # ✅ Only include major or minor files
        ]
        
        if not midi_files:
            messagebox.showerror("Error", f"No {key_type} MIDI files found in 'midi_files' directory!")
            return

        # Convert MIDI files to training data
        all_states = []
        for midi_file in midi_files:
            midi_data = midi_utils.load_midi(midi_file)
            parsed_notes = midi_utils.parse_midi(midi_data, midi_file)
            all_states += midi_utils.create_states(parsed_notes)

        # Train separate Markov Chain for major & minor
        markov_chain = MarkovChain()
        markov_chain.create_state_dictionary(all_states)
        markov_chain.create_transition_matrix(all_states)

        # Generate a solo
        sequence_length = 32 * num_bars
        generated_sequence = markov_chain.generate_sequence(sequence_length)

        # Transpose to user's key
        transposed_sequence = midi_utils.transpose_to_key(generated_sequence, key)

        # Save as MIDI
        file_name = f"midi_creations/{key}_{key_type}_{tempo}_{num_bars}.mid"
        midi_utils.create_midi_file(transposed_sequence, file_name, tempo)

        messagebox.showinfo("Success", f"Generated solo saved as '{file_name}'!")

    def run(self):
        """Runs the Tkinter event loop."""
        self.window.mainloop()


# Run the application
if __name__ == "__main__":
    app = MusicGeneratorApp()
    app.run()
