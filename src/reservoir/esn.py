"""
Reservoir Computing - Echo State Network
Implements the core ESN dynamics for temporal pattern processing.
"""
import numpy as np
import logging
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("Reservoir")


class EchoStateNetwork:
    """
    Echo State Network with Deep Tree structure.
    Implements hierarchical reservoir computing for temporal pattern recognition.
    """
    
    def __init__(self, input_dim: int, reservoir_dim: int = 256, output_dim: int = 64,
                 spectral_radius: float = 0.95, sparsity: float = 0.9,
                 leak_rate: float = 0.3, seed: int = 42):
        """
        Initialize the Echo State Network.
        
        Args:
            input_dim: Dimension of input signals
            reservoir_dim: Number of reservoir neurons
            output_dim: Dimension of output
            spectral_radius: Controls reservoir dynamics stability
            sparsity: Fraction of zero connections in reservoir
            leak_rate: Leaky integrator rate (0=no memory, 1=no leak)
            seed: Random seed for reproducibility
        """
        self.input_dim = input_dim
        self.reservoir_dim = reservoir_dim
        self.output_dim = output_dim
        self.spectral_radius = spectral_radius
        self.leak_rate = leak_rate
        
        np.random.seed(seed)
        
        # Input weights (sparse random)
        self.W_in = np.random.randn(reservoir_dim, input_dim) * 0.1
        
        # Reservoir weights (sparse, scaled to spectral radius)
        W = np.random.randn(reservoir_dim, reservoir_dim)
        mask = np.random.random((reservoir_dim, reservoir_dim)) > sparsity
        W *= mask
        # Scale to desired spectral radius
        eigenvalues = np.linalg.eigvals(W)
        max_eigenvalue = np.max(np.abs(eigenvalues))
        if max_eigenvalue > 0:
            W = W * (spectral_radius / max_eigenvalue)
        self.W_res = W
        
        # Output weights (trained via ridge regression)
        self.W_out = np.zeros((output_dim, reservoir_dim))
        
        # Reservoir state
        self.state = np.zeros(reservoir_dim)
        
        # Training data collection
        self._states_collected = []
        self._targets_collected = []
        
        logger.info(f"ESN initialized: {input_dim}→{reservoir_dim}→{output_dim} (ρ={spectral_radius})")
        
    def step(self, input_signal: np.ndarray) -> np.ndarray:
        """
        Advance reservoir by one timestep.
        
        Args:
            input_signal: Input vector of shape (input_dim,)
            
        Returns:
            Output vector of shape (output_dim,)
        """
        # Pre-activation: input + recurrent
        pre_activation = self.W_in @ input_signal + self.W_res @ self.state
        
        # Leaky integrator update with tanh nonlinearity
        self.state = (1 - self.leak_rate) * self.state + self.leak_rate * np.tanh(pre_activation)
        
        # Output
        output = self.W_out @ self.state
        return output
        
    def collect_state(self, input_signal: np.ndarray, target: Optional[np.ndarray] = None):
        """Collect reservoir state for training."""
        self.step(input_signal)
        self._states_collected.append(self.state.copy())
        if target is not None:
            self._targets_collected.append(target)
            
    def train(self, regularization: float = 1e-6):
        """
        Train output weights using ridge regression on collected states.
        
        Args:
            regularization: Ridge regression regularization parameter
        """
        if not self._states_collected or not self._targets_collected:
            logger.warning("No training data collected!")
            return
            
        states = np.array(self._states_collected)
        targets = np.array(self._targets_collected)
        
        # Ridge regression: W_out = Y^T * X * (X^T * X + λI)^-1
        XtX = states.T @ states + regularization * np.eye(self.reservoir_dim)
        XtY = states.T @ targets
        self.W_out = np.linalg.solve(XtX, XtY).T
        
        # Compute training error
        predictions = states @ self.W_out.T
        mse = np.mean((predictions - targets) ** 2)
        logger.info(f"Training complete. MSE: {mse:.6f}")
        
        # Clear collected data
        self._states_collected = []
        self._targets_collected = []
        
    def reset(self):
        """Reset reservoir state to zero."""
        self.state = np.zeros(self.reservoir_dim)
        
    def get_lyapunov_exponent(self, input_sequence: np.ndarray, perturbation: float = 1e-8) -> float:
        """
        Estimate the largest Lyapunov exponent of the reservoir dynamics.
        Positive = chaotic, Negative = stable/periodic.
        """
        self.reset()
        original_states = []
        
        for inp in input_sequence:
            self.step(inp)
            original_states.append(self.state.copy())
            
        # Perturb and re-run
        self.reset()
        self.state[0] += perturbation
        perturbed_states = []
        
        for inp in input_sequence:
            self.step(inp)
            perturbed_states.append(self.state.copy())
            
        # Compute divergence
        divergences = [np.linalg.norm(o - p) for o, p in zip(original_states, perturbed_states)]
        if divergences[-1] > 0 and divergences[0] > 0:
            lyapunov = np.log(divergences[-1] / max(divergences[0], 1e-12)) / len(input_sequence)
        else:
            lyapunov = 0.0
            
        return lyapunov


class HierarchicalESN:
    """
    Deep Tree Echo - Hierarchical ESN with tree-structured reservoirs.
    Multiple ESN layers with different timescales for multi-scale temporal processing.
    """
    
    def __init__(self, input_dim: int, layer_dims: Tuple[int, ...] = (128, 64, 32),
                 output_dim: int = 16):
        """
        Initialize hierarchical ESN with multiple timescale layers.
        
        Args:
            input_dim: Input dimension
            layer_dims: Tuple of reservoir dimensions per layer
            output_dim: Final output dimension
        """
        self.layers = []
        prev_dim = input_dim
        
        for i, dim in enumerate(layer_dims):
            # Each deeper layer has slower dynamics (higher leak rate)
            leak = 0.2 + 0.2 * i  # 0.2, 0.4, 0.6...
            spectral = 0.99 - 0.05 * i  # 0.99, 0.94, 0.89...
            
            esn = EchoStateNetwork(
                input_dim=prev_dim,
                reservoir_dim=dim,
                output_dim=dim,
                spectral_radius=spectral,
                leak_rate=leak
            )
            self.layers.append(esn)
            prev_dim = dim
            
        # Final readout
        self.readout = EchoStateNetwork(
            input_dim=prev_dim,
            reservoir_dim=32,
            output_dim=output_dim,
            spectral_radius=0.8,
            leak_rate=0.5
        )
        
        logger.info(f"Hierarchical ESN: {len(self.layers)} layers + readout")
        
    def step(self, input_signal: np.ndarray) -> np.ndarray:
        """Process input through all hierarchical layers."""
        x = input_signal
        for layer in self.layers:
            x = layer.step(x)
        return self.readout.step(x)
        
    def reset(self):
        """Reset all layers."""
        for layer in self.layers:
            layer.reset()
        self.readout.reset()


if __name__ == "__main__":
    # Demo: Simple pattern learning
    logger.info("=== ESN Demo: Sine Wave Prediction ===")
    
    esn = EchoStateNetwork(input_dim=1, reservoir_dim=100, output_dim=1)
    
    # Generate training data (predict next value of sine wave)
    t = np.linspace(0, 10 * np.pi, 1000)
    signal = np.sin(t)
    
    # Collect states
    for i in range(len(signal) - 1):
        esn.collect_state(
            input_signal=np.array([signal[i]]),
            target=np.array([signal[i + 1]])
        )
        
    # Train
    esn.train()
    
    # Test prediction
    esn.reset()
    predictions = []
    for i in range(100):
        pred = esn.step(np.array([signal[i]]))
        predictions.append(pred[0])
        
    error = np.mean((np.array(predictions) - signal[1:101]) ** 2)
    logger.info(f"Test MSE: {error:.6f}")
    
    # Lyapunov exponent
    test_input = np.array([[signal[i]] for i in range(200)])
    lyap = esn.get_lyapunov_exponent(test_input)
    logger.info(f"Lyapunov Exponent: {lyap:.4f} ({'chaotic' if lyap > 0 else 'stable'})")
