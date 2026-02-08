"""
Teaching Policy DQN Training Pipeline

Trains a Deep Q-Network to select optimal teaching interventions
based on student cognitive state.
"""

import argparse
from pathlib import Path
import numpy as np


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class StudentEnv:
    """Simple student cognitive-state environment (Gymnasium-like API)."""

    STATE_DIM = 8  # cognitive_load, mastery, engagement, fatigue, errors, time, modality_idx, streak
    N_ACTIONS = 7   # BREAK, SWITCH_MODALITY, SIMPLIFY, ENCOURAGE, GAMIFY, PEER_HELP, REVIEW

    def __init__(self):
        self.state = None
        self.steps = 0

    def reset(self):
        self.state = np.array([
            np.random.uniform(0.2, 0.8),   # cognitive_load
            np.random.uniform(0.1, 0.5),   # mastery
            np.random.uniform(0.4, 0.9),   # engagement
            np.random.uniform(0.0, 0.3),   # fatigue
            np.random.uniform(0, 5) / 10,  # error_rate
            0.0,                            # normalised time
            np.random.randint(0, 4) / 4,   # modality index
            0.0,                            # streak
        ], dtype=np.float32)
        self.steps = 0
        return self.state.copy()

    def step(self, action: int):
        cog, mastery, engage, fatigue, errors, t, mod, streak = self.state
        reward = 0.0

        # ---- crude transition dynamics ----
        if action == 0:  # BREAK
            fatigue = max(0, fatigue - 0.15)
            cog = max(0, cog - 0.1)
            reward += 0.1
        elif action == 1:  # SWITCH_MODALITY
            mod = (mod + 0.25) % 1.0
            cog = max(0, cog - 0.05)
            reward += 0.05
        elif action == 2:  # SIMPLIFY
            cog = max(0, cog - 0.15)
            mastery += 0.02
            reward += 0.1
        elif action == 3:  # ENCOURAGE
            engage = min(1, engage + 0.1)
            reward += 0.05
        elif action == 4:  # GAMIFY
            engage = min(1, engage + 0.15)
            reward += 0.08
        elif action == 5:  # PEER_HELP
            mastery += 0.03
            reward += 0.06
        elif action == 6:  # REVIEW
            mastery += 0.04
            cog += 0.05
            reward += 0.07

        # drift
        fatigue = min(1, fatigue + 0.02)
        cog = min(1, cog + 0.01)
        t += 0.05
        errors = max(0, errors - 0.01) if mastery > 0.5 else min(1, errors + 0.01)
        streak = (streak + 0.1) if errors < 0.3 else 0

        self.state = np.array([cog, mastery, engage, fatigue, errors, t, mod, streak], dtype=np.float32)
        self.steps += 1
        done = self.steps >= 50 or mastery >= 0.9
        if mastery >= 0.9:
            reward += 1.0
        return self.state.copy(), reward, done, {}


# ---------------------------------------------------------------------------
# DQN Agent
# ---------------------------------------------------------------------------

def build_dqn(state_dim: int, n_actions: int):
    """Build a simple DQN with PyTorch."""
    import torch
    import torch.nn as nn

    return nn.Sequential(
        nn.Linear(state_dim, 128),
        nn.ReLU(),
        nn.Linear(128, 128),
        nn.ReLU(),
        nn.Linear(128, n_actions),
    )


class ReplayBuffer:
    """Fixed-size experience replay buffer."""

    def __init__(self, capacity: int = 10_000):
        self.capacity = capacity
        self.buffer: list = []
        self.pos = 0

    def push(self, s, a, r, s2, done):
        item = (s, a, r, s2, done)
        if len(self.buffer) < self.capacity:
            self.buffer.append(item)
        else:
            self.buffer[self.pos] = item
        self.pos = (self.pos + 1) % self.capacity

    def sample(self, batch_size: int):
        idxs = np.random.choice(len(self.buffer), batch_size, replace=False)
        batch = [self.buffer[i] for i in idxs]
        s, a, r, s2, d = zip(*batch)
        return (
            np.array(s, dtype=np.float32),
            np.array(a, dtype=np.int64),
            np.array(r, dtype=np.float32),
            np.array(s2, dtype=np.float32),
            np.array(d, dtype=np.float32),
        )

    def __len__(self):
        return len(self.buffer)


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def train(epochs: int = 200, lr: float = 1e-3, gamma: float = 0.99,
          batch_size: int = 64, eps_start: float = 1.0, eps_end: float = 0.05,
          eps_decay: int = 150, output_dir: str = "ml/models/teaching_policy_dqn"):
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
    except ImportError:
        print("PyTorch not installed. Run: pip install torch")
        return

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    env = StudentEnv()
    policy_net = build_dqn(env.STATE_DIM, env.N_ACTIONS)
    target_net = build_dqn(env.STATE_DIM, env.N_ACTIONS)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=lr)
    buf = ReplayBuffer(20_000)

    total_rewards: list[float] = []

    for ep in range(1, epochs + 1):
        state = env.reset()
        ep_reward = 0.0
        done = False

        while not done:
            # epsilon-greedy
            eps = eps_end + (eps_start - eps_end) * np.exp(-ep / eps_decay)
            if np.random.rand() < eps:
                action = np.random.randint(env.N_ACTIONS)
            else:
                with torch.no_grad():
                    q = policy_net(torch.tensor(state).unsqueeze(0))
                    action = int(q.argmax(dim=1).item())

            next_state, reward, done, _ = env.step(action)
            buf.push(state, action, reward, next_state, float(done))
            state = next_state
            ep_reward += reward

            # learn
            if len(buf) >= batch_size:
                s, a, r, s2, d = buf.sample(batch_size)
                s_t = torch.tensor(s)
                a_t = torch.tensor(a).unsqueeze(1)
                r_t = torch.tensor(r).unsqueeze(1)
                s2_t = torch.tensor(s2)
                d_t = torch.tensor(d).unsqueeze(1)

                q_vals = policy_net(s_t).gather(1, a_t)
                with torch.no_grad():
                    next_q = target_net(s2_t).max(dim=1, keepdim=True).values
                target_q = r_t + gamma * next_q * (1 - d_t)

                loss = nn.functional.smooth_l1_loss(q_vals, target_q)
                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(policy_net.parameters(), 1.0)
                optimizer.step()

        total_rewards.append(ep_reward)

        # update target net periodically
        if ep % 10 == 0:
            target_net.load_state_dict(policy_net.state_dict())

        if ep % 20 == 0:
            avg = np.mean(total_rewards[-20:])
            print(f"Episode {ep}/{epochs}  avg_reward={avg:.3f}  eps={eps:.3f}")

    # save
    torch.save(policy_net.state_dict(), out / "policy_net.pt")
    print(f"Model saved to {out / 'policy_net.pt'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--output", default="ml/models/teaching_policy_dqn")
    args = parser.parse_args()
    train(epochs=args.epochs, lr=args.lr, output_dir=args.output)
