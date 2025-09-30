# MiniSynth v1.2

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org) [![NumPy](https://img.shields.io/badge/Numpy-777BB4?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org) [![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/KostasTopouzis/MiniSynth)

A simple, multi-octave synthesizer built with Python. This version introduces a real-time audio engine with a non-blocking callback architecture, allowing for sustained notes. This project serves as a foundational example of GUI development and real-time audio handling, created as part of a guided career development journey.

---
## Screenshot

[![MiniSynth v1.2 Screenshot](docs/images/mini_synth_v1.2.png)](https://youtu.be/MS1P31mTOy8)

---
## 🎹 Features (v1.2)

* A multi-octave keyboard GUI built with Tkinter.
* A real-time, callback-based audio engine for low-latency sound.
* Note-on and note-off handling for sustained sine wave tones.
* Thread-safe audio parameter updates using `threading.Lock`.

---
## 🛠️ Technologies Used

* **Python 3:** The core programming language.
* **Tkinter / ttk:** For building the graphical user interface.
* **PyAudio:** For handling the audio stream to the sound card.
* **NumPy:** For generating the sine wave audio data.
* **Git & GitHub:** For version control.

---
## 🚀 How to Run

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
    python mini_synth_v1.2.py
    ```

---
## 🔜 Future Goals

* **Object-Oriented GUI:** Encapsulate the keyboard creation logic into its own dedicated class.
* **Waveform Selection:** Add the ability to switch between sine, square, and sawtooth waves.

---
## 🐛 Troubleshooting

### UnicodeEncodeError on Windows

On some Windows systems, the default terminal cannot display special Unicode characters (like the `♭` symbol) and may crash with a `UnicodeEncodeError`. If you encounter this, here are two solutions:

1.  **Run from the Command Line with the UTF-8 flag:**
    Execute the script using this command instead of the standard one:
    ```bash
    python -X utf8 mini_synth_v1.2.py
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
## 📝 License

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

This project is distributed under the MIT License. See the `LICENSE` file for the full text and details.

---
## 📫 How to Reach Me

I'm always open to connecting with other developers and musicians or discussing potential collaborations. Please feel free to reach out.

* **Email:** `kostas.topouzis.dev@gmail.com`
