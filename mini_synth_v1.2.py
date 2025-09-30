"""
MiniSynth v1.2

A simple, multi-octave synthesizer built with Python's Tkinter GUI 
toolkit and the PyAudio library. It features a basic synthesis engine 
that generates sine wave tones for each key. This project serves as a 
foundational example of GUI development for audio applications.

Author: Kostas Topouzis
Date: 30 September 2025
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import pyaudio
import threading

# --- Definitions of constants ---

# Version number (MAJOR.MINOR.PATCH format)
APP_VERSION = "1.2"

# --- Audio Configuration ---
SAMPLE_RATE = 44100  # Samples per second
BUFFER_SIZE = 1024   # Number of frames per buffer

# Dimensions of keys (unit: pixel) for GUI layout
WHITE_KEY_WIDTH = 80
WHITE_KEY_HEIGHT = 280
BLACK_KEY_WIDTH = 40
BLACK_KEY_HEIGHT = 180

# Unicode characters for musical accidentals for display purposes
FLAT = "\u266d"
NATURAL = "\u266e"

# Note names for one octave. Black keys include both 
# sharp and flat names.
WHITE_KEYS_NOTES = ["C", "D", "E", "F", "G", "A", "B"]
BLACK_KEYS_NOTES = [
    f"C#\nD{FLAT}", f"D#\nE{FLAT}", f"F#\nG{FLAT}", 
    f"G#\nA{FLAT}", f"A#\nB{FLAT}"
]

# Octave width and number of octaves for the keyboard
OCTAVE_WIDTH = len(WHITE_KEYS_NOTES) * WHITE_KEY_WIDTH   
NUM_OCTAVES = 2

# Offsets of white and black keys
OFFSET_WH = [0, 2, 4, 5, 7, 9, 11]
OFFSET_BL = [1, 3, 6, 8, 10]

# Zero-based indices of white keys after which a black key is placed
BLACK_KEYS_POSITIONS = [0, 1, 3, 4, 5]


# --- Definition of the AudioEngine class ---
class AudioEngine:
    def __init__(self, sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32,
                                  channels=1,
                                  rate=sample_rate,
                                  output=True,
                                  stream_callback=self.audio_callback,
                                  frames_per_buffer=buffer_size)

        # Generate all 128 MIDI note frequencies
        self.midi_frequencies = [
            440 * (2**((n - 69) / 12)) for n in range(128)
        ]

        self.current_frequency = 0.0
        self.phase = 0
        self.sample_rate = sample_rate
        self.lock = threading.Lock()  # For safe access from threads

    # Audio callback function
    def audio_callback(self, in_data, frame_count, time_info, status):
        """
        Continuously called by PyAudio to get 
        the next chunk of audio.
        """
        with self.lock:
            t = np.arange(self.phase, self.phase + frame_count)
            angle = 2 * np.pi * self.current_frequency * t / self.sample_rate
            wave = 0.3 * np.sin(angle)
            self.phase += frame_count
        return (wave.astype(np.float32).tobytes(), pyaudio.paContinue)

    def note_on(self, midi_note_number):
        """Activates a note by its MIDI number."""
        with self.lock:
            # Check if the MIDI note number is within the valid range (0-127)
            if 0 <= midi_note_number < 128:
                self.current_frequency = self.midi_frequencies[midi_note_number]
                self.phase = 0   # Reset phase to avoid clicking

    def note_off(self, event=None):
        """Deactivates the sound by setting the frequency to zero."""
        with self.lock:
            self.current_frequency = 0.0

    def start(self):
        """Starts the audio stream."""
        self.stream.start_stream()

    def close(self):
        """Stops and closes the audio stream and terminates PyAudio."""
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()


#--------------------------------------------------
#                --- Main Application ---
# -------------------------------------------------

def main():
    """
    Main function to create and run the MiniSynth GUI
    and start the audio engine.
    """
    # Start the audio engine
    audio_engine = AudioEngine(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
    audio_engine.start()

    # --- GUI configuration ---
    # Create main application window ("root")
    root = tk.Tk()
    root.title(f"MiniSynth v{APP_VERSION}")

    # Calculate window width based on number of white keys
    window_width = NUM_OCTAVES * OCTAVE_WIDTH
    root.geometry(f"{window_width}x{WHITE_KEY_HEIGHT}")
    root.resizable(False, False)

    # Implement keyboard frame
    keyboard_frame = ttk.Frame(root, width=window_width, height=WHITE_KEY_HEIGHT)
    keyboard_frame.grid(row=1, column=0)


    # Lists to store the button widgets
    white_keys = []
    black_keys = []

    # Outer loop for number of octaves, inner ones 
    # for white and black keys
    for i in range(NUM_OCTAVES):
        # Create white keys
        for j, note in enumerate(WHITE_KEYS_NOTES):
            x_pos = j * WHITE_KEY_WIDTH + i * OCTAVE_WIDTH
            midi_note = 60 + i * 12 + OFFSET_WH[j]
            key = ttk.Button(keyboard_frame, text=note, style="White.TButton")
            key.place(x=x_pos, y=0, width=WHITE_KEY_WIDTH, height=WHITE_KEY_HEIGHT)
            # 60=C4. If you want the keyboard to begin on a different C, change this number
            key.bind("<ButtonPress-1>", lambda event, n=midi_note: audio_engine.note_on(n))
            key.bind("<ButtonRelease-1>", audio_engine.note_off)  # Calling note_off() upon release
            white_keys.append(key)
        
        # Black keys
        for j, (pos, note) in enumerate(zip(BLACK_KEYS_POSITIONS, BLACK_KEYS_NOTES)):
            key = tk.Button(keyboard_frame, text=note, fg="white", bg="black", 
                            activebackground="black", activeforeground="white", relief="raised", borderwidth=2
            )
            # Positioned relative to preceding white key
            x_pos = (pos * WHITE_KEY_WIDTH) + (WHITE_KEY_WIDTH - BLACK_KEY_WIDTH / 2) + (i * OCTAVE_WIDTH)
            midi_note = 60 + i * 12 + OFFSET_BL[j]
            key.place(x=x_pos, y=0, width=BLACK_KEY_WIDTH, height=BLACK_KEY_HEIGHT)
            key.bind("<ButtonPress-1>", lambda event, n=midi_note: audio_engine.note_on(n))
            key.bind("<ButtonRelease-1>", audio_engine.note_off)
            black_keys.append(key)

    # Configure styles for ttk widgets
    style = ttk.Style()
    style.configure("White.TButton", background="black", foreground="black")
    
    # Initialize main event loop
    root.mainloop()

    # Shut off the audio engine
    audio_engine.close()


# --- Entry Point ---
if __name__ == "__main__":
    main()