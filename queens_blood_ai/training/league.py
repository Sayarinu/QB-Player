
import os
import torch
import glob
import random
from .network import QueensBloodNetwork

class League:
    def __init__(self, save_dir, device, network_args):
        self.save_dir = save_dir
        self.device = device
        self.network_args = network_args
        self.opponents = []
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        self.refresh_league()
        
    def refresh_league(self):
        """Scans the save directory for model checkpoints."""
        files = glob.glob(os.path.join(self.save_dir, "*.pth"))
        self.opponents = files
        print(f"League refreshed. Found {len(self.opponents)} potential opponents.")
        
    def save_checkpoint(self, model, iteration):
        """Saves current model to league."""
        filename = os.path.join(self.save_dir, f"model_{iteration}.pth")
        
        # Save only state dict to save space and time
        torch.save(model.state_dict(), filename)
        # Avoid clutter: keep only last 10? Or keep all exponential?
        # For now, keep all. User can clean up.
        self.opponents.append(filename)
        
    def get_opponent_network(self):
        """Loads a random opponent network. Returns None if no opponents exist."""
        if not self.opponents:
            return None
            
        path = random.choice(self.opponents)
        
        # Instantiate a new network
        net = QueensBloodNetwork(*self.network_args).to(self.device)
        try:
            # We saved only state_dict in save_checkpoint
            # But the main trainer saves full checkpoint dict.
            # Handle both.
            checkpoint = torch.load(path, map_location=self.device)
            if 'model_state_dict' in checkpoint:
                net.load_state_dict(checkpoint['model_state_dict'])
            else:
                net.load_state_dict(checkpoint)
            net.eval()
            return net
        except Exception as e:
            print(f"Failed to load opponent {path}: {e}")
            return None
