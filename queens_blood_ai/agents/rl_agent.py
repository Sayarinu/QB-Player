import torch
import numpy as np
from typing import Tuple, Optional
from .base_agent import BaseAgent
from ..training.network import QueensBloodNetwork

class RLAgent(BaseAgent):
    def __init__(self, player_id: int, model_path: Optional[str] = None, num_cards: int = 145):
        super().__init__(player_id)
        # Using fixed shapes for now based on board size 3x5 and 5 features
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = QueensBloodNetwork(board_shape=(5, 3, 5), hand_size=10, num_cards=num_cards, num_actions=151).to(self.device)
        if model_path:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

    def select_action(self, state: dict, legal_moves: list) -> Optional[Tuple[int, int, int]]:
        board_tensor = torch.FloatTensor(state["board"]).unsqueeze(0).to(self.device)
        hand_tensor = torch.LongTensor(state["hand"]).unsqueeze(0).to(self.device)
        turn_tensor = torch.FloatTensor([[state["turn"]]]).to(self.device)
        
        with torch.no_grad():
            logits, value = self.model(board_tensor, hand_tensor, turn_tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
            
        # Action masking
        mask = np.zeros(151, dtype=bool)
        # Convert legal_moves [(idx, r, c)] to flat indices
        for card_idx, r, c in legal_moves:
            flat_idx = card_idx * 15 + (r * 5 + c)
            mask[flat_idx] = True
        mask[150] = True # Pass is always legal if no moves? Or always legal.
        
        # Apply mask
        masked_probs = probs * mask
        if masked_probs.sum() == 0:
            return None # Pass
            
        masked_probs /= masked_probs.sum()
        action_idx = np.random.choice(151, p=masked_probs)
        
        if action_idx == 150:
            return None
        
        card_idx = action_idx // 15
        pos_idx = action_idx % 15
        return (card_idx, pos_idx // 5, pos_idx % 5)
