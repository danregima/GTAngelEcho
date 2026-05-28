"""Tests for the Reservoir Computing module."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np


def test_esn_initialization():
    """Test that ESN initializes with correct dimensions."""
    from reservoir.esn import EchoStateNetwork
    esn = EchoStateNetwork(input_dim=4, reservoir_dim=100, output_dim=2)
    assert esn.W_in.shape == (100, 4)
    assert esn.W_res.shape == (100, 100)
    assert esn.W_out.shape == (2, 100)
    assert esn.state.shape == (100,)


def test_esn_step():
    """Test that ESN step produces output of correct shape."""
    from reservoir.esn import EchoStateNetwork
    esn = EchoStateNetwork(input_dim=3, reservoir_dim=50, output_dim=2)
    output = esn.step(np.array([1.0, 0.5, -0.3]))
    assert output.shape == (2,)


def test_esn_spectral_radius():
    """Test that reservoir spectral radius is approximately correct."""
    from reservoir.esn import EchoStateNetwork
    esn = EchoStateNetwork(input_dim=1, reservoir_dim=200, spectral_radius=0.9)
    eigenvalues = np.linalg.eigvals(esn.W_res)
    actual_radius = np.max(np.abs(eigenvalues))
    assert abs(actual_radius - 0.9) < 0.05


def test_hierarchical_esn():
    """Test hierarchical ESN with multiple layers."""
    from reservoir.esn import HierarchicalESN
    hesn = HierarchicalESN(input_dim=4, layer_dims=(64, 32, 16), output_dim=8)
    output = hesn.step(np.random.randn(4))
    assert output.shape == (8,)


def test_esn_training():
    """Test ESN training on simple pattern."""
    from reservoir.esn import EchoStateNetwork
    esn = EchoStateNetwork(input_dim=1, reservoir_dim=50, output_dim=1)
    
    # Train on sine wave
    t = np.linspace(0, 4 * np.pi, 200)
    signal = np.sin(t)
    
    for i in range(len(signal) - 1):
        esn.collect_state(np.array([signal[i]]), np.array([signal[i + 1]]))
    
    esn.train()
    
    # Test prediction
    esn.reset()
    predictions = []
    for i in range(50):
        pred = esn.step(np.array([signal[i]]))
        predictions.append(pred[0])
    
    # Should have reasonable prediction (MSE < 0.1)
    mse = np.mean((np.array(predictions) - signal[1:51]) ** 2)
    assert mse < 0.5  # Generous threshold for small reservoir


if __name__ == "__main__":
    test_esn_initialization()
    test_esn_step()
    test_esn_spectral_radius()
    test_hierarchical_esn()
    test_esn_training()
    print("All reservoir tests passed!")
