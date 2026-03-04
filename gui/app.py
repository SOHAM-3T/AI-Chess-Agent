from flask import Flask, render_template, request, jsonify
import sys
import os
import chess

# Add parent directory to path so we can import sunfish
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sunfish

app = Flask(__name__)

# Global board state
# In a real multi-user app, this should be stored per session
board = chess.Board()

# Searcher instance
searcher = sunfish.Searcher()

def get_sunfish_move(fen):
    """
    Given a FEN, ask Sunfish for the best move.
    """
    # Convert FEN to Sunfish board representation
    # Sunfish doesn't parse FEN natively in a way exposed easily, 
    # so we'll just play the moves from the startpos if possible,
    # OR simpler: just assume we are playing a game from start and track moves.
    # BUT, to be robust, let's use the current board state passed from client if needed.
    # Actually, simpler integration: We keep our own python-chess board, 
    # push the move, then convert the board to Sunfish's history format.
    
    # Reset sunfish history
    # Converting arbitrary FEN to sunfish history is tricky because of 3-fold repetition check.
    # For this simple GUI, we will just rely on the python-chess board 
    # and re-building sunfish history from the 'board.move_stack'.
    
    # 1. Initialize sunfish history
    hist = [sunfish.Position(sunfish.initial, 0, (True, True), (True, True), 0, 0)]
    
    # 2. Replay all moves from the python-chess board to sunfish
    for move in board.move_stack:
        # Convert python-chess move to sunfish parseable string
        # e.g. "e2e4"
        move_str = move.uci()
        
        # Parse logic from sunfish.py
        # def parse(c): ...
        try:
            f, r = ord(move_str[0]) - ord("a"), int(move_str[1]) - 1
            i = sunfish.A1 + f - 10 * r
            
            f, r = ord(move_str[2]) - ord("a"), int(move_str[3]) - 1
            j = sunfish.A1 + f - 10 * r
            
            prom = move_str[4].upper() if len(move_str) > 4 else ""
            
            # Sunfish board orientation flip for black
            # if ply % 2 == 1: i, j = 119 - i, 119 - j
            ply = len(hist) - 1 # History has startpos, so len 1 = ply 0
            if ply % 2 == 1:
                i, j = 119 - i, 119 - j
                
            hist.append(hist[-1].move(sunfish.Move(i, j, prom)))
        except Exception as e:
            print(f"Error parsing move {move_str}: {e}")
            return None

    # 3. Search
    # Copied from sunfish.py 'go' command logic
    # Set a small fixed time for responsiveness
    think_time = 1.0 # seconds
    
    start = sunfish.time.time()
    move_str = None
    best_move = None
    
    for depth, gamma, score, move in searcher.search(hist):
        if score >= gamma:
            if move is None:
                continue
                
            i, j = move.i, move.j
            if len(hist) % 2 == 1: # Black to move (sunfish perspective in search is always white-ish?)
                 # Wait, sunfish.py logic:
                 # if len(hist) % 2 == 0: i, j = 119 - i, 119 - j
                 pass
            
            # Render logic from sunfish.py
            # def render(i): ...
            # We need to map back to UCI
            if len(hist) % 2 == 0: # White to move in history means we need to flip if... 
                 # Let's look at sunfish.py: 
                 # if len(hist) % 2 == 0: i, j = 119 - i, 119 - j
                 i, j = 119 - i, 119 - j

            # Render
            move_str = sunfish.render(i) + sunfish.render(j) + move.prom.lower()
            # print("info", depth, score, move_str)
            
        if sunfish.time.time() - start > think_time:
            break
            
    return move_str

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def move():
    global board
    data = request.json
    uci = data.get('move')
    
    # 1. Apply user move to our board
    try:
        move = chess.Move.from_uci(uci)
        if move in board.legal_moves:
            board.push(move)
        else:
            return jsonify({'error': 'Illegal move', 'fen': board.fen()}), 400
    except:
        return jsonify({'error': 'Invalid format', 'fen': board.fen()}), 400
        
    if board.is_game_over():
        return jsonify({'fen': board.fen(), 'game_over': True, 'result': board.result()})

    # 2. Get Engine Move
    engine_move_uci = get_sunfish_move(board.fen())
    
    if engine_move_uci:
        engine_move = chess.Move.from_uci(engine_move_uci)
        board.push(engine_move)
    
    return jsonify({
        'fen': board.fen(), 
        'engine_move': engine_move_uci,
        'game_over': board.is_game_over(),
        'result': board.result() if board.is_game_over() else None
    })

@app.route('/newgame', methods=['POST'])
def newgame():
    global board
    board = chess.Board()
    
    data = request.json or {}
    color = data.get('color', 'white')
    
    if color == 'black':
        # Engine plays first
        engine_move_uci = get_sunfish_move(board.fen())
        if engine_move_uci:
            engine_move = chess.Move.from_uci(engine_move_uci)
            board.push(engine_move)
            return jsonify({'fen': board.fen(), 'engine_move': engine_move_uci})
            
    return jsonify({'fen': board.fen()})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
