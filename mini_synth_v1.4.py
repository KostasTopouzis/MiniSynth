"""
MiniSynth v1.4

A polyphonic synthesizer with a multi-octave piano keyboard GUI, built using
Python, Tkinter, and PyAudio.

This version features a significant architectural refactoring, separating the
application into a polyphonic `AudioEngine` class and a `MiniSynthGUI` class.
The audio engine supports multiple simultaneous voices, each with its own
ADSR (Attack, Decay, Sustain, Release) envelope for dynamic sound shaping.

Key Features:
- Polyphonic audio engine for playing chords and overlapping notes.
- Per-voice ADSR envelope for detailed control over sound dynamics.
- A scalable, multi-octave GUI keyboard built with Tkinter.
- Real-time, callback-based audio generation for low latency.
- Object-oriented design.

Author: Konstantinos Topouzis
Date: 15/11/2025
"""

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkFont
import numpy as np
import pyaudio
import threading
from typing import Dict, Optional

# --------------------------------
# --- Definitions of constants ---
# --------------------------------

# Version number (MAJOR.MINOR.PATCH format)
APP_VERSION = "1.4"

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


# --- Small utility: convert human-friendly note names to MIDI numbers ---
def note_name_to_midi(name: str, default_octave: int = 4) -> Optional[int]:
    """
    Convert a note name (examples: "C", "C#", "D♭", "A4", "C#\nD♭") to a MIDI
    note number (0-127). If the octave is omitted, `default_octave` is used.

    Returns the MIDI note number or None if parsing failed.
    """
    if not isinstance(name, str) or not name:
        return None

    # If label contains a newline (like "C#\nD♭"), take the first token
    token = name.split("\n")[0].strip()

    # Normalize unicode flat to ASCII 'b'
    token = token.replace("\u266d", "b")  # ♭ -> b
    token = token.replace("\u266e", "")   # natural sign -> ignore

    # Extract octave if present (e.g., C4, A#3)
    octave = None
    # Find trailing digits
    i = len(token) - 1
    while i >= 0 and token[i].isdigit():
        i -= 1
    if i < len(token) - 1:
        octave_part = token[i+1:]
        try:
            octave = int(octave_part)
            token = token[:i+1]
        except ValueError:
            octave = None

    if octave is None:
        octave = default_octave

    token = token.strip().upper()

    # Map note names to semitone offsets
    base_names = {
        'C': 0, 'C#': 1, 'DB': 1,
        'D': 2, 'D#': 3, 'EB': 3,
        'E': 4, 'F': 5, 'F#': 6, 'GB': 6,
        'G': 7, 'G#': 8, 'AB': 8,
        'A': 9, 'A#': 10, 'BB': 10,
        'B': 11
    }

    # Normalize flats written as 'B' after letter, e.g., 'DB' already
    token = token.replace('#', '#').replace('B', 'B')

    if token not in base_names:
        return None

    semitone = base_names[token]
    # MIDI note for C in octave 0 is 12
    midi = (octave + 1) * 12 + semitone
    if 0 <= midi <= 127:
        return midi
    return None


# --- Audio Engine with ADSR Envelope ---
class AudioEngine:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.sample_rate = SAMPLE_RATE
        self.stream = self.p.open(format=pyaudio.paFloat32,
                                  channels=1,
                                  rate=self.sample_rate,
                                  output=True,
                                  stream_callback=self.audio_callback,
                                  frames_per_buffer=BUFFER_SIZE)
        self.midi_frequencies = [440.0 * (2 ** ((n - 69) / 12)) for n in range(128)]
        self.note_frequencies = {
            "C": 261.63, "C#\nD♭": 277.18, "D": 293.66, "D#\nE♭": 311.13, "E": 329.63,
            "F": 349.23, "F#\nG♭": 369.99, "G": 392.00, "G#\nA♭": 415.30, "A": 440.00,
            "A#\nB♭": 466.16, "B": 493.88
        }
        self.lock = threading.Lock()
        # --- ADSR Envelope Parameters ---
        self.master_volume = 0.5
        self.attack_time = 1.5  # seconds
        self.decay_time = 1.2   # seconds
        self.release_time = 2.8 # seconds
        self.sustain_level = 0.3
        # --- Polyphonic Voice State ---
        # Each voice: { 'midi': int, 'freq': float, 'phase': int, 'env_state': str, 'env_level': float, 'env_pos': float }
        self.voices = []  # List of active voices

    def audio_callback(self, in_data, frame_count, time_info, status):
        with self.lock:
            if not self.voices:
                # No active voices, output silence
                return (np.zeros(frame_count, dtype=np.float32).tobytes(), pyaudio.paContinue)

            out = np.zeros(frame_count, dtype=np.float32)
            voices_to_remove = []
            for idx, voice in enumerate(self.voices):
                # Prepare time array for this voice
                t = np.arange(voice['phase'], voice['phase'] + frame_count)
                wave = np.sin(2 * np.pi * voice['freq'] * t / self.sample_rate)
                # Envelope calculation (per-sample, per-voice)
                env = np.zeros(frame_count, dtype=np.float32)
                env_level = voice['env_level']
                env_state = voice['env_state']
                for i in range(frame_count):
                    if env_state == 'attack':
                        env_level += 1.0 / (self.attack_time * self.sample_rate)
                        if env_level >= 1.0:
                            env_level = 1.0
                            env_state = 'decay'
                    elif env_state == 'decay':
                        env_level -= 1.0 / (self.decay_time * self.sample_rate)
                        if env_level <= self.sustain_level:
                            env_level = self.sustain_level
                            env_state = 'sustain'
                    elif env_state == 'sustain':
                        env_level = self.sustain_level
                    elif env_state == 'release':
                        env_level -= 1.0 / (self.release_time * self.sample_rate)
                        if env_level <= 0.0:
                            env_level = 0.0
                            env_state = 'off'
                    else:  # 'off'
                        env_level = 0.0
                    env[i] = env_level
                # Update voice state for next callback
                voice['env_level'] = float(env_level)
                voice['env_state'] = env_state
                voice['phase'] += frame_count
                # Mix this voice into output
                out += wave * env
                # If envelope is finished, mark for removal
                if env_state == 'off' and env_level <= 0.0:
                    voices_to_remove.append(idx)
            # Remove finished voices (from last to first to avoid index shift)
            for idx in reversed(voices_to_remove):
                del self.voices[idx]
            # Apply master volume
            out *= self.master_volume
            # Prevent clipping
            out = np.clip(out, -1.0, 1.0)
            return out.astype(np.float32).tobytes(), pyaudio.paContinue

    def note_on(self, midi_note_number):
        """
        Start a note by MIDI note number. Polyphonic: each note press adds a new voice.
        If the same note is already playing, retrigger its envelope (or add another voice).
        """
        with self.lock:
            # Accept int MIDI numbers primarily
            if isinstance(midi_note_number, int):
                if 0 <= midi_note_number < len(self.midi_frequencies):
                    freq = self.midi_frequencies[midi_note_number]
                else:
                    freq = 0.0
            else:
                freq = self.note_frequencies.get(midi_note_number, 0.0)
            # Add a new voice for this note
            voice = {
                'midi': midi_note_number,
                'freq': freq,
                'phase': 0,
                'env_state': 'attack',
                'env_level': 0.0,
            }
            self.voices.append(voice)

    def note_on_name(self, name: str, default_octave: int = 4) -> Optional[int]:
        """
        Convenience adapter: accept a human-friendly note name, convert to MIDI,
        call the numeric `note_on` API and return the MIDI number or None.
        This is safe to call from GUI code (not from the audio callback).
        """
        midi = note_name_to_midi(name, default_octave=default_octave)
        if midi is None:
            return None
        self.note_on(midi)
        return midi

    def note_off(self, event=None):
        """
        Release all voices (notes) currently playing. For true polyphony, you may want to
        track which key was released and only release that note. For now, this releases all.
        """
        with self.lock:
            for voice in self.voices:
                if voice['env_state'] not in ('release', 'off'):
                    voice['env_state'] = 'release'

    def start(self):
        self.stream.start_stream()

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()


class MiniSynthGUI:
    """
    The main GUI application for the MiniSynth.
    """
    def __init__(self, audio_engine: AudioEngine) -> None:
        # Start the audio engine
        self.audio_engine = audio_engine
        
        # --- GUI configuration ---
        self.root = tk.Tk()
        self.root.title(f"Mini Synth v{APP_VERSION}")

        self.WHITE_KEY_HEIGHT,self.WHITE_KEY_WIDTH, self.BLACK_KEY_HEIGHT, self.BLACK_KEY_WIDTH = self.calc_dimensions()

        self.white_font, self.black_font = self._setup_styles()
        self._setup_keyboard(self.WINDOW_WIDTH)

    def calc_dimensions(self):
        # --- Relative GUI Sizing ---
        # Define keys' dimensions as a percentage of the screen width for scalability
        screen_width = self.root.winfo_screenwidth()
        WHITE_KEY_WIDTH = screen_width // 38 # Fix the keys' dimensions to a minimum that 
                                            # is visually appealing in tkinter. Keys' dimensions
                                            # remain constant irrespective of keyboard size.
                                            # Up to 5-and-a-half octaves fit in the screen.
        self.WINDOW_WIDTH = int(WHITE_KEY_WIDTH * NUM_WHITE_KEYS)

        # Calculate key dimensions relative to the window size
        WHITE_KEY_HEIGHT = int(WHITE_KEY_WIDTH * 3.5) # Maintain a pleasant aspect ratio
        BLACK_KEY_WIDTH = int(WHITE_KEY_WIDTH * 0.5)
        BLACK_KEY_HEIGHT = int(BLACK_KEY_WIDTH * 4.5)

        # Set the final window geometry
        self.root.geometry(f"{self.WINDOW_WIDTH}x{WHITE_KEY_HEIGHT}")
        self.root.resizable(False, False)
        return WHITE_KEY_HEIGHT, WHITE_KEY_WIDTH, BLACK_KEY_HEIGHT, BLACK_KEY_WIDTH

    def _setup_styles(self) -> None:
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
        style = ttk.Style()
        style.configure("White.TButton", background="black", foreground="black", font=white_font)

        return white_font, black_font
    
    def _setup_keyboard(self, window_width: int) -> None:
        keyboard_frame = ttk.Frame(self.root, width=window_width, height=self.WHITE_KEY_HEIGHT)
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
            
            x_pos = i * self.WHITE_KEY_WIDTH
            
            key = ttk.Button(keyboard_frame, text=note, style="White.TButton")
            key.place(x=x_pos, y=0, width=self.WHITE_KEY_WIDTH, height=self.WHITE_KEY_HEIGHT)
            # Bind the GUI keys to the audio engine so pressing a key produces sound
            key.bind("<ButtonPress-1>", lambda event, n=midi_note: self.audio_engine.note_on(n))
            key.bind("<ButtonRelease-1>", self.audio_engine.note_off)
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

                x_pos = (i * self.WHITE_KEY_WIDTH) + (self.WHITE_KEY_WIDTH - self.BLACK_KEY_WIDTH / 2)
                
                key = tk.Button(keyboard_frame, text=note, font=self.black_font, fg="white", bg="black",
                            activebackground="black", activeforeground="white", relief="raised", borderwidth=2
                )
                key.place(x=x_pos, y=0, width=self.BLACK_KEY_WIDTH, height=self.BLACK_KEY_HEIGHT)
                # Bind black keys as well
                key.bind("<ButtonPress-1>", lambda event, n=midi_note: self.audio_engine.note_on(n))
                key.bind("<ButtonRelease-1>", self.audio_engine.note_off)
                black_keys.append(key)

                # Increment the counter for the next black key
                index += 1

    def run(self) -> None:
        """Starts the Tkinter main loop."""
        self.root.mainloop()

def main() -> None:
    """
    Entry point for the MiniSynth application.
    """
    audio_engine = AudioEngine()
    audio_engine.start()
    gui = MiniSynthGUI(audio_engine)
    try:
        gui.run()
    finally:
        audio_engine.close()

if __name__ == "__main__":
    main()
