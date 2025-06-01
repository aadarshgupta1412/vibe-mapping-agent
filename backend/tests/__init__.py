# Tests package for vibe-mapping-agent backend
"""
Test suite for the Vibe Mapping Agent backend.

This package contains:
- unit/: Unit tests for individual components
- integration/: Integration tests for component interactions  
- e2e/: End-to-end tests for full workflows

Test Structure:
- core/: Tests for core functionality (database, config)
- services/: Tests for service layer (tools, agent processor)
- routes/: Tests for API routes
- models/: Tests for data models
"""

import os
import sys
import pytest
from pathlib import Path

# Add the parent directory to Python path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Test configuration
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest settings."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )

# Tests for vibe-mapping-agent backend 