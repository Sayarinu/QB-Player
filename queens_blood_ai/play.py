import argparse
import time
import json
import sys
import os
import torch
import numpy as np
from torch.distributions import Categorical
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from queens_blood_ai.game.game import Game, Player
from queens_blood_ai.game.deck import Deck
from queens_blood_ai.game.card import Card
from queens_blood_ai.training.network import QueensBloodNetwork

# Load env variables including DEVICE
load_dotenv()

def load_cards(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return [Card.from_dict(d) for d in data]

def load_decks(path):
    with open(path, 'r') as f:
        return json.load(f)

def get_observation(game, card_db):
    """
    Reconstructs the observation tensor from the game state.
    Must match QueensBloodEnv._get_obs EXACTLY.
    """
    board_obs = np.zeros((5, 3, 5), dtype=np.float32)
    
    # Layer 0: P1 Ranks
    # Layer 1: P2 Ranks
    board_obs[0] = game.board.ranks[Player.PLAYER1] / 3.0
    board_obs[1] = game.board.ranks[Player.PLAYER2] / 3.0
    
    # Layer 2: Ownership (1 for P1, -1 for P2)
    for r in range(3):
        for c in range(5):
            owner = game.board.owner[r, c]
            if owner == Player.PLAYER1.value: board_obs[2, r, c] = 1.0
            elif owner == Player.PLAYER2.value: board_obs[2, r, c] = -1.0
    
    # Layer 3: Card Power
    # Layer 4: Card ID (normalized)
    for r in range(3):
        for c in range(5):
            card = game.board.cards[r][c]
            if card:
                board_obs[3, r, c] = card.adjusted_power / 20.0
                board_obs[4, r, c] = getattr(card, 'id', 0) / len(card_db)

    hand_obs = np.zeros(10, dtype=np.int32)
    hand = game.players[game.current_turn]["hand"]
    for i in range(min(len(hand), 10)):
        card_name = hand[i].name
        for idx, c_ref in enumerate(card_db):
            if c_ref.name == card_name:
                hand_obs[i] = idx + 1
                break
        
    turn_obs = np.array([1 if game.current_turn == Player.PLAYER1 else 0], dtype=np.int32)
    
    return {
        "board": torch.tensor(board_obs, dtype=torch.float32).unsqueeze(0),
        "hand": torch.tensor(hand_obs, dtype=torch.long).unsqueeze(0),
        "turn": torch.tensor(turn_obs, dtype=torch.long).unsqueeze(0) # (1, 1)
    }

def decode_action(action_idx, game):
    if action_idx == 150:
        return None
    
    card_idx = action_idx // 15
    pos_idx = action_idx % 15
    row = pos_idx // 5
    col = pos_idx % 5
    
    hand = game.players[game.current_turn]["hand"]
    if card_idx < len(hand):
        return (card_idx, row, col)
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--model", type=str, default="queens_blood_model.pth")
    parser.add_argument("--deterministic", action="store_true")
    args = parser.parse_args()
    
    # Device setup
    device_name = os.getenv("DEVICE", "auto").lower()
    if device_name == "cuda" and torch.cuda.is_available(): device = torch.device("cuda")
    elif device_name == "mps" and torch.backends.mps.is_available(): device = torch.device("mps")
    elif device_name == "cpu": device = torch.device("cpu")
    else: device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    
    print(f"Using device: {device}")

    try:
        cards = load_cards("queens_blood_ai/data/cards_database.json")
    except FileNotFoundError:
        print("Error: Could not find cards_database.json")
        return

    # Load Decks
    decks_data = load_decks("queens_blood_ai/data/decks.json")
    deck_names = list(decks_data.keys())
    deck1_cards = [cards[cid] for cid in decks_data[deck_names[0]]]
    deck2_cards = [cards[cid] for cid in decks_data[deck_names[1]]]
    
    # Initialize Model
    model = QueensBloodNetwork(
        board_shape=(5, 3, 5),
        hand_size=10,
        num_cards=len(cards),
        num_actions=151
    ).to(device)
    
    if os.path.exists(args.model):
        print(f"Loading model: {args.model}")
        checkpoint = torch.load(args.model, map_location=device)
        # Handle both full checkpoint dict and direct state_dict
        if 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
        model.eval()
    else:
        print(f"Error: Model file {args.model} not found.")
        return

    deck1 = Deck(deck1_cards)
    deck2 = Deck(deck2_cards)
    game = Game(deck1, deck2)
    
    print("Game Started!")
    
    while not game.game_over:
        # Prepare Input
        obs = get_observation(game, cards)
        b = obs['board'].to(device)
        h = obs['hand'].to(device)
        t = obs['turn'].to(device) # Needs (1, 1) or (1,) depending on forward?
        if t.dim() == 1: t = t.unsqueeze(1) # Ensure (1, 1)
        
        # Inference
        with torch.no_grad():
            logits, val = model(b, h, t)
            
            # Action Masking (Essential for Play)
            # Set logits of illegal moves to -inf
            logits = logits.squeeze(0) # (151,)
            
            # Iterate all actions
            legal_mask = torch.full_like(logits, -float('inf'))
            found_legal = False
            
            for act_idx in range(151):
                decoded = decode_action(act_idx, game)
                if decoded is None: # Pass requires check? Assume pass is always legal if no moves?
                     # Actually game.step(None) is valid pass.
                     if act_idx == 150:
                         legal_mask[act_idx] = 0 # Pass is neutral preference unless forced
                         found_legal = True
                else:
                    c_idx, r, c = decoded
                    hand = game.players[game.current_turn]["hand"]
                    card = hand[c_idx]
                    if game.is_legal_move(game.current_turn, card, r, c):
                        legal_mask[act_idx] = logits[act_idx] # Keep original logit
                        found_legal = True
            
            # If we found legal moves, we sample from them. 
            # If only pass is legal, we pass.
            
            probs = torch.softmax(legal_mask, dim=0)
            
            if args.deterministic:
                action_idx = torch.argmax(probs).item()
            else:
                dist = Categorical(probs)
                action_idx = dist.sample().item()
        
        # Execute
        decoded = decode_action(action_idx, game)
        if decoded:
            card = game.players[game.current_turn]["hand"][decoded[0]]
            print(f"Player {game.current_turn} plays {card.name} at {decoded[1:]}")
            game.step(decoded)
        else:
            print(f"Player {game.current_turn} passes.")
            game.step(None)
            
        if args.render:
            # Simple ASCII render
            for r in range(game.board.height):
                row_str = ""
                for c in range(game.board.width):
                    owner = game.board.get_owner(r, c)
                    owner_name = "P1" if owner == Player.PLAYER1 else "P2" if owner == Player.PLAYER2 else ".."
                    rank = game.board.get_rank(r, c, owner) if owner != Player.NEUTRAL else 0
                    card = game.board.cards[r][c]
                    
                    if card:
                        power_str = f"{card.adjusted_power:2d}"
                        name_str = card.name[:3]
                    else:
                        power_str = "  "
                        name_str = "   "
                        
                    row_str += f"[{owner_name} R{rank} {name_str}:{power_str}] "
                print(row_str)
            print("-" * 20)
            time.sleep(1)

    s1, s2 = game.get_final_scores()
    print(f"Game Over! Final Score: P1 {s1} - P2 {s2}")

if __name__ == "__main__":
    main()
