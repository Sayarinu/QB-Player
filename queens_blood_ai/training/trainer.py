import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions import Categorical
from .environment import QueensBloodEnv
from .network import QueensBloodNetwork
import numpy as np
import yaml
from tqdm import tqdm

class PPOTrainer:
    def __init__(self, config_path: str, card_db: list):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.env = QueensBloodEnv(card_db)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.model = QueensBloodNetwork(
            board_shape=(5, 3, 5), 
            hand_size=10, 
            num_cards=len(card_db), 
            num_actions=151
        ).to(self.device)
        
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.config['ppo']['learning_rate'])
        self.save_path = self.config['training'].get('save_path', 'queens_blood_model.pth')
        
        # Load existing model if available
        self.load_model()
        
    def train(self):
        total_its = self.config['training']['num_iterations']
        games_per_it = self.config['training'].get('games_per_iteration', 10)
        
        for it in tqdm(range(total_its)):
            all_episodes = []
            for _ in range(games_per_it):
                all_episodes.append(self.collect_rollouts())
            
            # Update policy
            self.update_policy(all_episodes)
            
            if (it + 1) % self.config['training']['evaluation_frequency'] == 0:
                self.evaluate()
                self.save_model()
        
        # Final save
        self.save_model()

    def collect_rollouts(self):
        episode = []
        obs, _ = self.env.reset()
        done = False
        
        while not done:
            # Convert obs to torch
            board = torch.FloatTensor(obs['board']).unsqueeze(0).to(self.device)
            hand = torch.LongTensor(obs['hand']).unsqueeze(0).to(self.device)
            turn = torch.LongTensor(obs['turn']).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                logits, value = self.model(board, hand, turn)
                probs = Categorical(logits=logits)
                action = probs.sample()
                log_prob = probs.log_prob(action)
            
            next_obs, reward, done, _, _ = self.env.step(action.item())
            
            episode.append({
                'obs': obs,
                'action': action,
                'log_prob': log_prob,
                'reward': reward,
                'value': value
            })
            obs = next_obs
            
        return episode

    def update_policy(self, episodes):
        if not episodes: return
        
        all_board_obs = []
        all_hand_obs = []
        all_turn_obs = []
        all_actions = []
        all_log_probs = []
        all_returns = []
        all_advantages = []

        gamma = self.config['ppo']['gamma']

        for episode in episodes:
            rewards = [step['reward'] for step in episode]
            values = [step['value'].item() for step in episode]
            
            # Calculate returns
            returns = []
            running_return = 0
            for r in reversed(rewards):
                running_return = r + gamma * running_return
                returns.insert(0, running_return)
            
            # Calculate advantages (simple version)
            episode_returns = torch.FloatTensor(returns).to(self.device)
            episode_values = torch.FloatTensor(values).to(self.device)
            advantages = episode_returns - episode_values
            
            for i, step in enumerate(episode):
                all_board_obs.append(torch.FloatTensor(step['obs']['board']))
                all_hand_obs.append(torch.LongTensor(step['obs']['hand']))
                all_turn_obs.append(torch.LongTensor(step['obs']['turn']))
                all_actions.append(step['action'])
                all_log_probs.append(step['log_prob'])
                all_returns.append(returns[i])
                all_advantages.append(advantages[i])

        # Convert to tensors
        board_b = torch.stack(all_board_obs).to(self.device)
        hand_b = torch.stack(all_hand_obs).to(self.device)
        turn_b = torch.stack(all_turn_obs).to(self.device) # Ensure (B, 1)
        action_b = torch.cat(all_actions).to(self.device)
        log_prob_b = torch.cat(all_log_probs).to(self.device)
        return_b = torch.FloatTensor(all_returns).to(self.device)
        adv_b = torch.stack(all_advantages).to(self.device)
        
        # Normalize advantages
        adv_b = (adv_b - adv_b.mean()) / (adv_b.std() + 1e-8)

        # Update model
        num_epochs = self.config['ppo'].get('epochs', 4)
        for _ in range(num_epochs):
            logits, values = self.model(board_b, hand_b, turn_b)
            probs = Categorical(logits=logits)
            new_log_probs = probs.log_prob(action_b)
            entropy = probs.entropy().mean()
            
            ratio = torch.exp(new_log_probs - log_prob_b)
            surr1 = ratio * adv_b
            surr2 = torch.clamp(ratio, 1.0 - self.config['ppo']['clip_epsilon'], 1.0 + self.config['ppo']['clip_epsilon']) * adv_b
            
            policy_loss = -torch.min(surr1, surr2).mean()
            value_loss = F.mse_loss(values.squeeze(), return_b)
            
            loss = policy_loss + 0.5 * value_loss - 0.01 * entropy
            
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

    def evaluate(self):
        print("Evaluating agent...")
        wins = 0
        num_games = 100
        for _ in range(num_games):
            obs, _ = self.env.reset()
            done = False
            while not done:
                board = torch.FloatTensor(obs['board']).unsqueeze(0).to(self.device)
                hand = torch.LongTensor(obs['hand']).unsqueeze(0).to(self.device)
                turn = torch.LongTensor(obs['turn']).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    logits, _ = self.model(board, hand, turn)
                    action = torch.argmax(logits, dim=1).item()
                obs, reward, done, _, _ = self.env.step(action)
                if done and reward > 0:
                    wins += 1
        print(f"Evaluation Win Rate: {wins/num_games * 100}%")
    def save_model(self):
        """Saves the model weights and optimizer state."""
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config
        }
        torch.save(checkpoint, self.save_path)
        print(f"Model saved to {self.save_path}")

    def load_model(self):
        """Loads model weights if a checkpoint exists."""
        if os.path.exists(self.save_path):
            print(f"Loading existing model from {self.save_path}...")
            checkpoint = torch.load(self.save_path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            print("Model loaded successfully.")
        else:
            print("No existing model found. Starting from scratch.")
