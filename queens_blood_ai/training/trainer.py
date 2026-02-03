
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions import Categorical
from .environment import QueensBloodEnv
from .network import QueensBloodNetwork
from .league import League
import numpy as np
import yaml
from tqdm import tqdm
import gymnasium as gym

class PPOTrainer:
    def __init__(self, config_path: str, card_db: list, continuous: bool = False):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        if continuous:
            print("Continuous training enabled. Setting iterations to infinity.")
            self.config['training']['num_iterations'] = 1000000000 # 1 Billion
        
        # Determine Device
        # Priority: Env Var > Auto Detect
        requested_device = os.getenv("DEVICE", "auto").lower()
        self.device = torch.device("cpu") # Default
        
        if requested_device == "cuda":
            if torch.cuda.is_available(): self.device = torch.device("cuda")
            else: print("WARNING: cuda requested but not available. Falling back to cpu.")
        elif requested_device == "mps":
            if torch.backends.mps.is_available(): self.device = torch.device("mps")
            else: print("WARNING: mps requested but not available. Falling back to cpu.")
        elif requested_device == "cpu":
            self.device = torch.device("cpu")
        else:
            # Auto
            if torch.cuda.is_available(): self.device = torch.device("cuda")
            elif torch.backends.mps.is_available(): self.device = torch.device("mps")
            
        print(f"Using device: {self.device} (Requested: {requested_device})")
        
        # Vectorized Environment Setup
        self.num_envs = self.config['training'].get('num_envs', 8)
        self.num_steps = self.config['training'].get('num_steps', 128)
        
        env_fns = [lambda: QueensBloodEnv(card_db) for _ in range(self.num_envs)]
        self.envs = gym.vector.AsyncVectorEnv(env_fns)
        
        # Network kwargs
        self.network_args = (
            (5, 3, 5), 
            10, 
            len(card_db), 
            151
        )
        
        self.model = QueensBloodNetwork(*self.network_args).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.config['ppo']['learning_rate'])
        self.save_path = self.config['training'].get('save_path', 'queens_blood_model.pth')
        
        # League Setup
        league_path = self.config['training'].get('league_path', 'league_checkpoints/')
        self.league = League(league_path, self.device, self.network_args)
        
        self.opponent_model = None # None = Self-Play (vs current model)
        
        # Learner Side Tracking (0=P1, 1=P2)
        # Randomly assign initial sides
        self.learner_sides = torch.randint(0, 2, (self.num_envs,), device=self.device)
        
        # Tracking variables
        self.global_step = 0
        self.obs, _ = self.envs.reset()
        
        # Load existing model if available
        self.load_model()
        
    def train(self):
        total_iterations = self.config['training']['num_iterations']
        update_freq = self.config['training'].get('update_frequency', 10)
        
        print(f"Starting training with {self.num_envs} environments...")
        for it in tqdm(range(total_iterations)):
            # League Management
            # 1. Periodically save to league
            if (it + 1) % self.config['training']['evaluation_frequency'] == 0:
                self.league.save_checkpoint(self.model, it+1)
                self.save_model()
                
            # 2. Periodically refresh opponent
            if (it + 1) % update_freq == 0:
                print("Refreshing opponent...")
                self.opponent_model = self.league.get_opponent_network()
                if self.opponent_model:
                    print("New opponent loaded from league.")
                else:
                    print("No opponent found in league, continuing Self-Play.")

            # Collect & Update
            rollouts = self.collect_rollouts()
            self.update_policy(rollouts)
            
        self.save_model()
        self.envs.close()

    def collect_rollouts(self):
        obs_board_list = []
        obs_hand_list = []
        obs_turn_list = []
        actions_list = []
        log_probs_list = []
        rewards_list = []
        dones_list = []
        values_list = []
        mask_list = [] # is_learner_turn mask
        
        for _ in range(self.num_steps):
            self.global_step += self.num_envs
            
            # Prepare inputs
            board = torch.tensor(self.obs['board'], dtype=torch.float32).to(self.device)
            hand = torch.tensor(self.obs['hand'], dtype=torch.long).to(self.device)
            turn = torch.tensor(self.obs['turn'], dtype=torch.long).to(self.device)
            if turn.dim() == 1: turn = turn.unsqueeze(1)
            
            # Determine turns
            # turn is (B, 1), 1=P1, 0=P2? 
            # Environment.py says: 1 if P1, 0 if P2?
            # Let's verify environment.py: 
            # "turn": np.array([1 if self.game.current_turn == Player.PLAYER1 else 0], dtype=np.int32)
            # Yes.
            # Convert to 0/1 index: P1=0, P2=1? 
            # No, turn=1 (P1), turn=0 (P2).
            # self.learner_sides: 1 (P1), 0 (P2) to match?
            # Let's standardize: 1=P1, 0=P2.
            
            current_player_is_p1 = (turn.squeeze() == 1)
            learner_is_p1 = (self.learner_sides == 1)
            
            # is_learner_turn: (Current is P1 AND Learner is P1) OR (Current is P2 AND Learner is P2)
            is_learner_turn = (current_player_is_p1 == learner_is_p1)
            
            # Action Selection
            actions = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
            log_probs = torch.zeros(self.num_envs, dtype=torch.float32, device=self.device)
            values = torch.zeros(self.num_envs, dtype=torch.float32, device=self.device)
            
            # 1. Learner Moves
            if is_learner_turn.any():
                with torch.no_grad():
                    l_logits, l_val = self.model(board[is_learner_turn], hand[is_learner_turn], turn[is_learner_turn])
                    l_probs = Categorical(logits=l_logits)
                    l_action = l_probs.sample()
                    l_log_prob = l_probs.log_prob(l_action)
                    
                    actions[is_learner_turn] = l_action
                    log_probs[is_learner_turn] = l_log_prob
                    values[is_learner_turn] = l_val.squeeze()
            
            # 2. Opponent Moves
            if (~is_learner_turn).any():
                with torch.no_grad():
                    # If opponent_model is None, use self.model (Self-Play)
                    opp_net = self.opponent_model if self.opponent_model else self.model
                    
                    o_logits, o_val = opp_net(board[~is_learner_turn], hand[~is_learner_turn], turn[~is_learner_turn])
                    o_probs = Categorical(logits=o_logits)
                    o_action = o_probs.sample()
                    
                    # We don't care about log_prob for opponent
                    actions[~is_learner_turn] = o_action
                    values[~is_learner_turn] = o_val.squeeze() # We track value for GAE continuity
            
            # Step Env
            cpu_action = actions.cpu().numpy()
            next_obs, rewards, terminations, truncations, infos = self.envs.step(cpu_action)
            dones = np.logical_or(terminations, truncations)
            
            # Handle Learner Side Flipping on Done
            if dones.any():
                # For envs that finished, flip the learner side for the NEW game
                # 0 -> 1, 1 -> 0
                self.learner_sides[dones] = 1 - self.learner_sides[dones]
            
            # Store
            obs_board_list.append(board)
            obs_hand_list.append(hand)
            obs_turn_list.append(turn)
            actions_list.append(actions)
            log_probs_list.append(log_probs)
            values_list.append(values)
            rewards_list.append(torch.tensor(rewards, dtype=torch.float32).to(self.device))
            dones_list.append(torch.tensor(dones, dtype=torch.float32).to(self.device))
            mask_list.append(is_learner_turn.float()) # 1.0 if learner, 0.0 if opponent
            
            self.obs = next_obs

        # Bootstrap Value
        board = torch.tensor(self.obs['board'], dtype=torch.float32).to(self.device)
        hand = torch.tensor(self.obs['hand'], dtype=torch.long).to(self.device)
        turn = torch.tensor(self.obs['turn'], dtype=torch.long).to(self.device)
        if turn.dim() == 1: turn = turn.unsqueeze(1)
            
        with torch.no_grad():
            # Use learner model for value estimation of next state always? 
            # Yes, we want V^pi(s)
            _, next_value = self.model(board, hand, turn)
            next_value = next_value.flatten()
            
        return {
            'board': torch.stack(obs_board_list),
            'hand': torch.stack(obs_hand_list),
            'turn': torch.stack(obs_turn_list),
            'actions': torch.stack(actions_list),
            'log_probs': torch.stack(log_probs_list),
            'rewards': torch.stack(rewards_list),
            'dones': torch.stack(dones_list),
            'values': torch.stack(values_list),
            'mask': torch.stack(mask_list),
            'next_value': next_value
        }

    def update_policy(self, rollouts):
        obs_board = rollouts['board']
        obs_hand = rollouts['hand']
        obs_turn = rollouts['turn']
        actions = rollouts['actions']
        log_probs = rollouts['log_probs']
        rewards = rollouts['rewards']
        dones = rollouts['dones']
        values = rollouts['values']
        mask = rollouts['mask']
        next_value = rollouts['next_value']
        
        # GAE
        gamma = self.config['ppo']['gamma']
        gae_lambda = self.config['ppo']['gae_lambda']
        
        advantages = torch.zeros_like(rewards).to(self.device)
        last_gae_lam = 0
        
        for t in reversed(range(self.num_steps)):
            if t == self.num_steps - 1:
                nextnonterminal = 1.0 - dones[t]
                nextvalues = next_value
            else:
                nextnonterminal = 1.0 - dones[t]
                nextvalues = values[t + 1]
                
            delta = rewards[t] + gamma * nextvalues * nextnonterminal - values[t]
            last_gae_lam = delta + gamma * gae_lambda * nextnonterminal * last_gae_lam
            advantages[t] = last_gae_lam
            
        returns = advantages + values
        
        # Flatten
        b_board = obs_board.reshape((-1,) + obs_board.shape[2:])
        b_hand = obs_hand.reshape((-1,) + obs_hand.shape[2:])
        b_turn = obs_turn.reshape((-1,) + obs_turn.shape[2:])
        b_actions = actions.reshape(-1)
        b_log_probs = log_probs.reshape(-1)
        b_advantages = advantages.reshape(-1)
        b_returns = returns.reshape(-1)
        b_values = values.reshape(-1)
        b_mask = mask.reshape(-1)
        
        # Optimization
        b_inds = np.arange(self.num_steps * self.num_envs)
        clip_epsilon = self.config['ppo']['clip_epsilon']
        entropy_coef = self.config['ppo']['entropy_coef']
        value_coef = self.config['ppo']['value_loss_coef']
        num_epochs = self.config['ppo']['epochs']
        minibatch_size = (self.num_steps * self.num_envs) // 4
        
        for _ in range(num_epochs):
            np.random.shuffle(b_inds)
            for start in range(0, len(b_inds), minibatch_size):
                end = start + minibatch_size
                mb_inds = b_inds[start:end]
                
                mb_mask = b_mask[mb_inds]
                # Skip batch if no learner steps (unlikely)
                if mb_mask.sum() == 0: continue
                
                mb_board = b_board[mb_inds]
                mb_hand = b_hand[mb_inds]
                mb_turn = b_turn[mb_inds]
                mb_actions = b_actions[mb_inds]
                mb_log_probs = b_log_probs[mb_inds]
                mb_advantages = b_advantages[mb_inds]
                mb_returns = b_returns[mb_inds]
                
                mb_advantages = (mb_advantages - mb_advantages.mean()) / (mb_advantages.std() + 1e-8)
                
                new_logits, new_values = self.model(mb_board, mb_hand, mb_turn)
                new_values = new_values.view(-1)
                
                new_probs = Categorical(logits=new_logits)
                new_log_probs = new_probs.log_prob(mb_actions)
                entropy = new_probs.entropy().mean()
                
                logregistry = new_log_probs - mb_log_probs
                ratio = torch.exp(logregistry)
                
                surr1 = ratio * mb_advantages
                surr2 = torch.clamp(ratio, 1.0 - clip_epsilon, 1.0 + clip_epsilon) * mb_advantages
                
                # MASKING: Only average loss over learner steps
                pg_loss = -torch.min(surr1, surr2)
                pg_loss = (pg_loss * mb_mask).sum() / (mb_mask.sum() + 1e-8)
                
                v_loss = 0.5 * ((new_values - mb_returns) ** 2)
                v_loss = (v_loss * mb_mask).sum() / (mb_mask.sum() + 1e-8)
                
                loss = pg_loss + value_coef * v_loss - entropy_coef * entropy
                
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

    def save_model(self):
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config
        }
        torch.save(checkpoint, self.save_path)
        
    def load_model(self):
        if os.path.exists(self.save_path):
            print(f"Loading existing model from {self.save_path}...")
            try:
                checkpoint = torch.load(self.save_path, map_location=self.device)
                self.model.load_state_dict(checkpoint['model_state_dict'])
                self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                print("Model loaded.")
            except:
                print("Failed to load model, starting from scratch.")
        else:
            print("No existing model found.")
