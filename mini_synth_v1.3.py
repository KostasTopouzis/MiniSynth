"""
MiniSynth v1.3

A simple, multi-octave synthesizer built with Python's Tkinter GUI 
toolkit and the PyAudio library. It features a basic synthesis engine 
that generates sine wave tones for each key.

Author: Kostas Topouzis
Date: 04 November 2025
"""

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkFont
import numpy as np
import pyaudio
import threading

# --------------------------------
# --- Definitions of constants ---
# --------------------------------

# Version number (MAJOR.MINOR.PATCH format)
APP_VERSION = "1.3"

# --- Audio Configuration ---
SAMPLE_RATE = 44100  # Samples per second
BUFFER_SIZE = 1024   # Number of frames per buffer

START_MIDI_NOTE = 36 # C2

# Offsets of white and black keys' MIDI notes
OFFSET_WH = [0, 2, 4, 5, 7, 9, 11]
OFFSET_BL = [1, 3, 6, 8, 10]

# Total number of white keys of the keyboard
NUM_WHITE_KEYS = 31

# Zero-based indices of white keys after which a black key is placed
BLACK_KEYS_POSITIONS = [0, 1, 3, 4, 5]

# --- Names ---
# Unicode characters for musical accidentals for display purposes
FLAT = "\u266d"
NATURAL = "\u266e"

# Note names for one octave. Black keys include both 
# sharp and flat names
WHITE_KEYS_NOTES = ["C", "D", "E", "F", "G", "A", "B"]
BLACK_KEYS_NOTES = [
    f"C#\nD{FLAT}", f"D#\nE{FLAT}", f"F#\nG{FLAT}", 
    f"G#\nA{FLAT}", f"A#\nB{FLAT}"
]


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

    # Get the default font family for the system
    # Get the default font family and size for the system and derive named fonts
    default_font = tkFont.nametofont("TkDefaultFont")
    default_family = default_font.actual().get("family", "TkDefaultFont")
    default_size = default_font.actual().get("size", 10)
    # Tk may return a negative size to indicate pixels; normalize to positive
    try:
        if isinstance(default_size, (int, float)) and default_size < 0:
            default_size = abs(int(default_size))
        else:
            default_size = int(default_size)
    except Exception:
        default_size = 10

    # Create named Font objects so we can reuse and adjust them dynamically.
    # White keys use the default size; black keys use a slightly smaller size
    # to fit two-line labels (e.g. "C#\nD♭"). Adjust the decrement as needed.
    white_font = tkFont.Font(family=default_family, size=default_size)
    black_font = tkFont.Font(family=default_family, size=max(default_size - 2, 6))

    # --- Relative GUI Sizing ---
    # Define keys' dimensions as a percentage of the screen width for scalability
    screen_width = root.winfo_screenwidth()
    WHITE_KEY_WIDTH = screen_width // 38 # Fix the keys' dimensions to a minimum that 
                                         # is visually appealing in tkinter. Keys' dimensions
                                         # remain constant irrespective of keyboard size.
                                         # Up to 5-and-a-half octaves fit in the screen.
    WINDOW_WIDTH = int(WHITE_KEY_WIDTH * NUM_WHITE_KEYS)

    # Calculate key dimensions relative to the window size
    WHITE_KEY_HEIGHT = int(WHITE_KEY_WIDTH * 3.5) # Maintain a pleasant aspect ratio
    BLACK_KEY_WIDTH = int(WHITE_KEY_WIDTH * 0.5)
    BLACK_KEY_HEIGHT = int(BLACK_KEY_WIDTH * 4.5)

    # Set the final window geometry
    root.geometry(f"{WINDOW_WIDTH}x{WHITE_KEY_HEIGHT}")
    root.resizable(False, False)

    # Implement keyboard frame
    keyboard_frame = ttk.Frame(root, width=WINDOW_WIDTH, height=WHITE_KEY_HEIGHT)
    keyboard_frame.grid(row=1, column=0)

    # Lists to store the button widgets
    white_keys = []
    black_keys = []

    # Create white keys
    for i in range(NUM_WHITE_KEYS):
        index_wh = i % 7
        note = WHITE_KEYS_NOTES[index_wh]
        midi_offset = OFFSET_WH[index_wh]

        octave_num = i // 7
        midi_note = START_MIDI_NOTE + (octave_num * 12) + midi_offset
        
        x_pos = i * WHITE_KEY_WIDTH
        
        key = ttk.Button(keyboard_frame, text=note, style="White.TButton")
        key.place(x=x_pos, y=0, width=WHITE_KEY_WIDTH, height=WHITE_KEY_HEIGHT)
        
        key.bind("<ButtonPress-1>", lambda event, n=midi_note: audio_engine.note_on(n))
        key.bind("<ButtonRelease-1>", audio_engine.note_off)
        white_keys.append(key)
        
    # Create black keys
    index = 0
    # NUM_WHITE_KEYS - 1 is used to avoid placing a black key off the end
    for i in range(NUM_WHITE_KEYS - 1):
        if (i % 7) in BLACK_KEYS_POSITIONS:
            index_bl = index % 5
            note = BLACK_KEYS_NOTES[index_bl]
            midi_offset = OFFSET_BL[index_bl]

            octave_num_bl = index // 5
            midi_note = START_MIDI_NOTE + (octave_num_bl * 12) + midi_offset

            x_pos = (i * WHITE_KEY_WIDTH) + (WHITE_KEY_WIDTH - BLACK_KEY_WIDTH / 2)
            
            key = tk.Button(keyboard_frame, text=note, font=black_font, fg="white", bg="black",
                        activebackground="black", activeforeground="white", relief="raised", borderwidth=2
            )
            key.place(x=x_pos, y=0, width=BLACK_KEY_WIDTH, height=BLACK_KEY_HEIGHT)

            key.bind("<ButtonPress-1>", lambda event, n=midi_note: audio_engine.note_on(n))
            key.bind("<ButtonRelease-1>", audio_engine.note_off)
            black_keys.append(key)

            # Increment the counter for the next black key
            index += 1                


    # Configure styles for ttk widgets
    style = ttk.Style()
    # Use the named font object for ttk white keys too so both tk and ttk widgets
    # share the same family and relative sizing.
    style.configure("White.TButton", background="black", foreground="black", font=white_font)
    
    # Initialize main event loop
    root.mainloop()

    # Shut off the audio engine
    audio_engine.close()


# --- Entry Point ---
if __name__ == "__main__":
    main()
