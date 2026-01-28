import pytest
from queens_blood_ai.game.board import Board, Player
from queens_blood_ai.game.card import Card

def test_board_init():
    board = Board()
    assert board.get_owner(0, 0) == Player.PLAYER1
    assert board.get_owner(0, 4) == Player.PLAYER2
    assert board.get_rank(0, 0, Player.PLAYER1) == 1
    assert board.get_rank(0, 4, Player.PLAYER2) == 1

def test_place_card():
    board = Board()
    # Simple card with pattern [0, 1]
    card = Card("Test", 1, 1, rank_positions=[(0, 1)])
    board.place_card(0, 0, card, Player.PLAYER1)
    
    assert board.cards[0][0] == card
    # Tile at (0, 1) should now be Player 1 with Rank 1
    assert board.get_owner(0, 1) == Player.PLAYER1
    assert board.get_rank(0, 1, Player.PLAYER1) == 1

def test_rank_up():
    board = Board()
    # P1 rank at (0,0) is 1
    board.update_rank(0, 0, Player.PLAYER1, 1)
    assert board.get_rank(0, 0, Player.PLAYER1) == 2
    
    board.update_rank(0, 0, Player.PLAYER1, 2) # max 3
    assert board.get_rank(0, 0, Player.PLAYER1) == 3
