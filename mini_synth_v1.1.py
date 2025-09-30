"""
MiniSynth, v1.1

A simple, multi-octave interactive piano keyboard built with Python's Tkinter library.
This project serves as a foundational example of GUI development for audio applications.

Author: Kostas Topouzis
Date: 30 September 2025
"""

import tkinter as tk
from tkinter import ttk

# --- Definitions of constants---

# Version number (MAJOR.MINOR.PATCH format)
APP_VERSION = "1.1"

# Dimensions of keys (unit: pixel) for GUI layout
WHITE_KEY_WIDTH = 80
WHITE_KEY_HEIGHT = 280
BLACK_KEY_WIDTH = 40
BLACK_KEY_HEIGHT = 180

# Unicode characters for musical accidentals for display purposes
FLAT = "\u266d"
NATURAL = "\u266e"

# Note names for one octave. Black keys include both sharp and flat names.
WHITE_KEYS_NOTES = ["C", "D", "E", "F", "G", "A", "B"]
BLACK_KEYS_NOTES =  [
    f"C#\nD{FLAT}", f"D#\nE{FLAT}", f"F#\nG{FLAT}", f"G#\nA{FLAT}", f"A#\nB{FLAT}"
]

# Octave width and number of octaves for the keyboard
OCTAVE_WIDTH = len(WHITE_KEYS_NOTES) * WHITE_KEY_WIDTH   
NUM_OCTAVES = 2

# Zero-based indices of white keys after which a black key is placed
BLACK_KEYS_POSITIONS = [0, 1, 3, 4, 5]


# --- Definitions of functions ---

def play_note(note):
    """
    Placeholder function that is called when a piano key is pressed.
    Currently, it just prints the note name to the console.
    """
    console_output = note.replace("\n", "/")
    print(f"Key pressed: {console_output}")

    
def main():
    """
    Main function to create and run the MiniSynth GUI application.
    """
    # Create main application window ("root")
    root = tk.Tk()
    root.title(f"MiniSynth v{APP_VERSION}")

    # Calculate window width based on number of white keys
    window_width = OCTAVE_WIDTH * NUM_OCTAVES
    root.geometry(f"{window_width}x{WHITE_KEY_HEIGHT}")
    root.resizable(False, False)   # Prevent the user from resizing the window

    # Keyboard frame implementation
    keyboard_frame = tk.Frame(root, width=window_width, height=WHITE_KEY_HEIGHT)
    keyboard_frame.pack()

    # Lists to store the button widgets
    white_keys = []
    black_keys = []

    # Outer loop for number of octaves, inner ones for white and black keys
    for i in range(NUM_OCTAVES):
        #Create white keys
        for j, note in enumerate(WHITE_KEYS_NOTES):
            key = ttk.Button(keyboard_frame, text=note, style="White.TButton", command=lambda n=note: play_note(n))
            key.place(x=j * WHITE_KEY_WIDTH + i * OCTAVE_WIDTH, y=0, width=WHITE_KEY_WIDTH, height=WHITE_KEY_HEIGHT)
            white_keys.append(key)

        # Create black keys
        for j, note in zip(BLACK_KEYS_POSITIONS, BLACK_KEYS_NOTES):
            key = tk.Button(keyboard_frame, text=note, bg="black", fg="white", activebackground="black", activeforeground="white", relief="raised", borderwidth=2, command=lambda n=note: play_note(n))
            key.place(x=(j * WHITE_KEY_WIDTH) + (WHITE_KEY_WIDTH - BLACK_KEY_WIDTH / 2 + i * OCTAVE_WIDTH), y=0, width=BLACK_KEY_WIDTH, height=BLACK_KEY_HEIGHT)
            black_keys.append(key)

    # Configure styles for ttk widgets
    style = ttk.Style()
    style.configure("White.TButton", background="black", foreground="black")

    # Initializing main event loop
    root.mainloop()


# --- Entry Point ---
# Ensures main() is called only when this script is executed
# directly, not when imported as a module
if __name__ == "__main__":
    main()
