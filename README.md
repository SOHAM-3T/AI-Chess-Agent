# Chess Agent with Web GUI

Ths is a simple, but strong chess engine, written in Python. This repository now includes a modern Web GUI to play against the engine easily.

## Quick Start (Play Game)

**Windows:**
Double-click `run_gui.bat` or run:
```powershell
.\run_gui.bat
```

This will launch a web server and automatically open the game in your browser.

## Features

-   **Clean Web Interface**: Play using drag-and-drop on a graphical board.
-   **Color Selection**: Play as White or Black.
-   **Strong Engine**: Uses the Sunfish Chess engine (approx. 2000+ ELO on Lichess).
-   **NNUE Support**: Includes an experimental neural network version (`sunfish_nnue.py`).

## Project Structure

-   `gui/`: Contains the Flask web application and frontend.
-   `sunfish.py`: The core chess engine (Classic version).
-   `sunfish_nnue.py`: Experimental NNUE version.
-   `sunfish_uci.py`: Shared UCI protocol logic.
-   `nnue/`: Neural network weights and data.

## Running the Engine Directly (UCI)

If you want to use Sunfish with other GUIs (like Arena, Banksia, etc.), you can run it as a standard UCI engine:

```bash
python sunfish.py uci
```

## NNUE Version

To experiment with the neural network version:

```bash
python sunfish_nnue.py nnue/models/tanh.pickle
```

