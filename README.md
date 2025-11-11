# MiniSynth v1.3.1

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org) [![NumPy](https://img.shields.io/badge/Numpy-777BB4?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org) [![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/KostasTopouzis/MiniSynth)

A simple, multi-octave synthesizer built with Python. This version extends the playable range from C2 to E6 while simultaneously reducing the overall keyboard size in order to improve the future integration of the MiniSynth in a professional music production working environment. It also improves label readability by deriving named fonts from the system default for consistent, DPI-aware sizing and calculates key proportions relative to the screenwidth to avoid visual distortion in different display settings.

See `CHANGELOG.md` for full release notes — latest: v1.3.1: Fix audible pop at note on/off (added short attack/release envelope; vectorized NumPy implementation).

---
## Screenshot

[![MiniSynth v1.3.1 Screenshot](docs/images/mini_synth_v1.3.1.png)](https://youtu.be/7Dj9_wVjeuQ)

---
## Features (v1.3.1)

* A multi-octave keyboard GUI built with Tkinter.
* A real-time, callback-based audio engine for low-latency sound.
* Note-on and note-off handling for sustained sine wave tones.
* Thread-safe audio parameter updates using `threading.Lock`.

---

## Technologies Used

* **Python 3:** The core programming language.
* **Tkinter / ttk:** For building the graphical user interface.
* **PyAudio:** For handling the audio stream to the sound card.
* **NumPy:** For generating the sine wave audio data.
* **Git & GitHub:** For version control.

---

## Performance & Benchmarks

This version uses **vectorized NumPy operations** for the amplitude envelope (attack/release) instead of per-sample Python loops. This design choice significantly reduces CPU overhead and latency jitter in real-time audio callbacks. The benchmark typically shows a **5-10x speedup** on modern CPUs, with even greater gains during sustain phases, demonstrating the importance of efficient numerical computing in audio applications.

To see the performance comparison between the per-sample and vectorized approaches and the real numbers for your system:

```bash
python benchmark_envelope.py
```

---

## How to Run

1.  Ensure you have Python 3 installed on your system.
2.  Clone this repository to your local machine:
    ```bash
    git clone [https://github.com/KostasTopouzis/MiniSynth.git](https://github.com/KostasTopouzis/MiniSynth.git)
    ```
3.  Navigate to the project directory:
    ```bash
    cd MiniSynth
    ```
4.  Run the main script:
    ```bash
    python mini_synth_v1.3.1.py
    ```

---
## Future Goals

* **Object-Oriented GUI:** Encapsulate the keyboard creation logic into its own dedicated class.
* **Waveform Selection:** Add the ability to switch between sine, square, and sawtooth waves.
* **Increased control and musical usufulness:** Add the ability to control through the computer keyboard and eventually a MIDI controller.

---
## Troubleshooting

### UnicodeEncodeError on Windows

On some Windows systems, the default terminal cannot display special Unicode characters (like the `♭` symbol) and may crash with a `UnicodeEncodeError`. If you encounter this, here are two solutions:

1.  **Run from the Command Line with the UTF-8 flag:**
    Execute the script using this command instead of the standard one:
    ```bash
    python -X utf8 mini_synth_v1.3.1.py
    ```

2.  **Configure VS Code's Runner (`launch.json`):**
    If you are running the file using the VS Code "Run" button, you can create a `.vscode/launch.json` file in your project with the following content to automatically enable UTF-8 mode for every run:
    ```json
    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Current File",
                "type": "python",
                "request": "launch",
                "program": "${file}",
                "console": "integratedTerminal",
                "justMyCode": true,
                "env": {
                    "PYTHONUTF8": "1"
                }
            }
        ]
    }
    ```

---
## License

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

This project is distributed under the MIT License. See the `LICENSE` file for the full text and details.

---
## How to Reach Me

I'm always open to connecting with other developers and musicians or discussing potential collaborations. Please feel free to reach out.

* **Email:** `kostas.topouzis.dev@gmail.com`
