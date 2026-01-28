from queens_blood_ai.game.game import Game, Player
from queens_blood_ai.game.deck import Deck
from queens_blood_ai.game.card import Card

def test_game_flow():
    # Setup simple game
    c1 = Card("P1_Card", 1, 2, rank_positions=[(0, 1)])
    c2 = Card("P2_Card", 1, 3, rank_positions=[(0, -1)])
    
    deck1 = Deck([c1] * 15)
    deck2 = Deck([c2] * 15)
    
    game = Game(deck1, deck2)
    
    # P1 Turn
    moves = game.get_legal_moves(Player.PLAYER1)
    assert len(moves) > 0
    game.step(moves[0])
    
    # Check board state
    assert game.board.cards[moves[0][1]][moves[0][2]] is not None
    assert game.current_turn == Player.PLAYER2

def test_legal_moves():
    c1 = Card("P1_Card", 3, 10) # High cost
    deck1 = Deck([c1] * 15)
    deck2 = Deck([c1] * 15)
    game = Game(deck1, deck2)
    
    # Should have no legal moves for a Rank 3 card because start ranks are 1
    moves = game.get_legal_moves(Player.PLAYER1)
    # Actually, card_idx, r, c
    # Check if any move's card cost is satisfied
    for m in moves:
        card = game.players[Player.PLAYER1]["hand"][m[0]]
        assert card.cost <= game.board.get_rank(m[1], m[2], Player.PLAYER1)
