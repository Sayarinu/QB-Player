import torch
import torch.nn as nn
import torch.nn.functional as F

class QueensBloodNetwork(nn.Module):
    def __init__(self, board_shape, hand_size, num_cards, num_actions):
        super().__init__()
        # Board CNN
        self.conv1 = nn.Conv2d(board_shape[0], 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        
        # Hand Embedding
        self.hand_embedding = nn.Embedding(num_cards + 1, 16)
        
        # Combined FC layers
        # 64 * 3 * 5 = 960 (from CNN)
        # 16 * 10 = 160 (from Hand)
        # 1 (from turn)
        self.fc1 = nn.Linear(960 + 160 + 1, 256)
        self.fc2 = nn.Linear(256, 256)
        
        # Output heads
        self.policy_head = nn.Linear(256, num_actions)
        self.value_head = nn.Linear(256, 1)

    def forward(self, board, hand, turn):
        # board: (B, 5, 3, 5)
        # hand: (B, 10)
        # turn: (B, 1)
        
        x_board = F.relu(self.conv1(board))
        x_board = F.relu(self.conv2(x_board))
        x_board = x_board.view(x_board.size(0), -1)
        
        x_hand = self.hand_embedding(hand) # (B, 10, 16)
        x_hand = x_hand.view(x_hand.size(0), -1) # (B, 160)
        
        combined = torch.cat([x_board, x_hand, turn.float()], dim=1)
        
        x = F.relu(self.fc1(combined))
        x = F.relu(self.fc2(x))
        
        logits = self.policy_head(x)
        value = self.value_head(x)
        
        return logits, value
