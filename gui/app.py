from flask import Flask, render_template, request, jsonify
import sys
import os
import subprocess
import chess

app = Flask(__name__)

# Global board state
# In a real multi-user app, this should be stored per session
board = chess.Board()
current_engine = "sunfish"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_engine_cmd(engine_name):
    if engine_name == "nnue":
        return [
            sys.executable,
            os.path.join(PROJECT_ROOT, "sunfish_nnue.py"),
            os.path.join(PROJECT_ROOT, "nnue", "models", "tanh.pickle"),
        ]
    return [sys.executable, os.path.join(PROJECT_ROOT, "sunfish.py")]


def get_engine_move(engine_name):
    moves = " ".join(move.uci() for move in board.move_stack)
    position_cmd = "position startpos" + (f" moves {moves}" if moves else "")
    uci_in = "\n".join(
        [
            "uci",
            "isready",
            position_cmd,
            "go movetime 900",
            "quit",
            "",
        ]
    )

    try:
        result = subprocess.run(
            get_engine_cmd(engine_name),
            input=uci_in,
            text=True,
            capture_output=True,
            timeout=15,
            cwd=PROJECT_ROOT,
        )
    except Exception as e:
        print(f"Engine launch failed ({engine_name}): {e}")
        return None

    if result.returncode != 0:
        print(f"Engine exited non-zero ({engine_name}): {result.stderr}")
        return None

    for line in reversed(result.stdout.splitlines()):
        if line.startswith("bestmove "):
            parts = line.split()
            if len(parts) >= 2 and parts[1] != "(none)":
                return parts[1]
            break
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def move():
    global board, current_engine
    data = request.json
    uci = data.get('move')
    engine = data.get('engine')
    if engine in ("sunfish", "nnue"):
        current_engine = engine
    
    # 1. Apply user move to our board
    try:
        move = chess.Move.from_uci(uci)
        if move in board.legal_moves:
            board.push(move)
        else:
            return jsonify({'error': 'Illegal move', 'fen': board.fen()}), 400
    except Exception:
        return jsonify({'error': 'Invalid format', 'fen': board.fen()}), 400
        
    if board.is_game_over():
        return jsonify({'fen': board.fen(), 'game_over': True, 'result': board.result()})

    # 2. Get Engine Move
    engine_move_uci = get_engine_move(current_engine)
    
    if engine_move_uci:
        try:
            engine_move = chess.Move.from_uci(engine_move_uci)
            if engine_move in board.legal_moves:
                board.push(engine_move)
            else:
                return jsonify({'error': 'Engine produced illegal move', 'fen': board.fen()}), 500
        except Exception:
            return jsonify({'error': 'Engine produced invalid move', 'fen': board.fen()}), 500
    
    return jsonify({
        'fen': board.fen(), 
        'engine_move': engine_move_uci,
        'game_over': board.is_game_over(),
        'result': board.result() if board.is_game_over() else None
    })

@app.route('/newgame', methods=['POST'])
def newgame():
    global board, current_engine
    board = chess.Board()
    
    data = request.json or {}
    color = data.get('color', 'white')
    engine = data.get('engine')
    if engine in ("sunfish", "nnue"):
        current_engine = engine
    
    if color == 'black':
        # Engine plays first
        engine_move_uci = get_engine_move(current_engine)
        if engine_move_uci:
            try:
                engine_move = chess.Move.from_uci(engine_move_uci)
                if engine_move in board.legal_moves:
                    board.push(engine_move)
                    return jsonify({'fen': board.fen(), 'engine_move': engine_move_uci})
            except Exception:
                pass
            
    return jsonify({'fen': board.fen()})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
