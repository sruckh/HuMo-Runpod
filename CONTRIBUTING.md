# CONTRIBUTING.md

## Code of Conduct

### Our Pledge
We as members, contributors, and leaders pledge to make participation in our community a harassment-free experience for everyone, regardless of age, body size, visible or invisible disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socioeconomic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards
Examples of behavior that contributes to creating a positive environment include:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Unacceptable Behavior
Examples of unacceptable behavior include:
- Trolling, insulting/derogatory comments, or personal/political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

## Development Setup

### Prerequisites
- Docker with NVIDIA GPU support
- Python 3.11+
- Git
- Hugging Face account with model access
- RunPod account (for deployment)

### Environment Setup
```bash
# Clone the repository
git clone https://github.com/your-username/HuMo.git
cd HuMo

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install the project in development mode
pip install -e .

# Setup pre-commit hooks
pre-commit install
```

### Docker Development Setup
```bash
# Build development container
docker build -t humo:dev -f Dockerfile.dev .

# Run development container
docker run --gpus all -p 7860:7860 -v $(pwd):/app humo:dev

# Access container shell
docker exec -it humo-dev /bin/bash
```

### Model Download Setup
```bash
# Login to Hugging Face CLI
huggingface-cli login

# Download required models
python scripts/download_models.py

# Verify model downloads
ls -la weights/
```

## Code Style Guide

### Python Code Style
```python
# Follow PEP 8 guidelines
# Use 4 spaces for indentation
# Maximum line length: 88 characters (Black default)
# Use type hints where appropriate

# Good example
from typing import Dict, List, Optional

def generate_video(
    prompt: str,
    audio_path: Optional[str] = None,
    image_path: Optional[str] = None,
    resolution: str = "480p"
) -> Dict[str, str]:
    """Generate video from text prompt and optional audio/image.

    Args:
        prompt: Text description for video generation
        audio_path: Path to audio file for synchronization
        image_path: Path to reference image for conditioning
        resolution: Output video resolution ("480p" or "720p")

    Returns:
        Dictionary containing video metadata and file paths
    """
    # Implementation
    pass
```

### Documentation Standards
```python
# Use Google-style docstrings
def process_video(video_path: str, output_dir: str) -> str:
    """Process video file and save to output directory.

    Args:
        video_path: Path to input video file
        output_dir: Directory to save processed video

    Returns:
        Path to processed video file

    Raises:
        FileNotFoundError: If input video doesn't exist
        ValueError: If video format is unsupported
    """
    # Implementation
    pass

# Add inline comments for complex logic
def calculate_optimal_batch_size(
    model_size: int,
    available_memory: int,
    safety_factor: float = 0.8
) -> int:
    """Calculate optimal batch size based on model memory requirements.

    Uses heuristic formula to maximize batch size while staying within
    memory limits with safety factor.
    """
    # Estimate memory per sample (rough heuristic)
    memory_per_sample = model_size * 1.2  # 20% overhead

    # Apply safety factor to available memory
    safe_memory = available_memory * safety_factor

    # Calculate maximum batch size
    max_batch_size = int(safe_memory / memory_per_sample)

    # Ensure minimum batch size of 1
    return max(1, max_batch_size)
```

### Error Handling Patterns
```python
# Use specific exception types
try:
    model = load_model(model_name)
except ModelNotFoundError as e:
    logger.error(f"Model not found: {e}")
    raise
except MemoryError as e:
    logger.error(f"Insufficient memory to load model: {e}")
    # Suggest reducing batch size or model size
    raise ConfigurationError("Consider reducing model size or batch size") from e

# Use context managers for resource management
with torch.no_grad():
    output = model.generate(input_data)

# Validate inputs early
def validate_input(prompt: str, audio_path: Optional[str] = None) -> None:
    """Validate input parameters."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    if audio_path and not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if len(prompt) > 1000:
        raise ValueError("Prompt too long (max 1000 characters)")
```

## Commit Message Format

### Commit Message Structure
```bash
# Format: <type>(<scope>): <description>
#
# Types:
# feat: New feature
# fix: Bug fix
# docs: Documentation changes
# style: Code style changes (formatting, etc.)
# refactor: Code refactoring (neither bug fix nor new feature)
# test: Test changes
# chore: Maintenance tasks (build process, dependency updates, etc.)

# Examples:
feat(inference): add text-to-image-audio mode support
fix(model): resolve memory leak in model unloading
docs(readme): update installation instructions
style(config): format configuration files
test(integration): add e2e pipeline tests
chore(deps): update pytorch to 2.5.1
```

### Detailed Commit Messages
```bash
# Detailed commit message body (optional)
feat(inference): add video upscaling capability

Add AI-powered video upscaling using ESRGAN model. Users can now
select output resolution up to 4K for generated videos.

Key changes:
- Integrate ESRGAN model for upscaling
- Add resolution selection to UI
- Implement progress tracking for upscaling process
- Add memory management for large resolution handling

Testing:
- Unit tests for upscaling pipeline
- Integration tests with existing video generation
- Performance tests for memory usage

Fixes #123
```

## Pull Request Process

### PR Checklist
- [ ] Code follows project style guidelines
- [ ] All tests pass (unit, integration, e2e)
- [ ] Documentation updated for new features
- [ ] Commit messages follow the format
- [ ] No sensitive information committed
- [ ] Performance impact assessed
- [ ] Security implications reviewed

### PR Template
```markdown
## Description
Brief description of the changes made in this pull request.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] E2E tests written and passing
- [ ] Manual testing performed

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] Any dependent changes have been merged and published in downstream modules

## Issues
Closes #123
Related to #456
```

### Review Process
1. **Self-Review**: Review your own code before submitting
2. **Automated Checks**: All CI/CD checks must pass
3. **Peer Review**: At least one reviewer from the team
4. **Security Review**: Required for changes involving authentication, model access, or container security
5. **Performance Review**: Required for changes affecting model performance or resource usage
6. **Documentation Review**: Ensure all changes are properly documented

## Testing Requirements

### New Feature Testing
```python
# Every new feature must have tests
def test_new_feature():
    """Test the new feature functionality"""
    # Arrange
    setup_test_environment()
    test_input = create_test_input()

    # Act
    result = new_feature(test_input)

    # Assert
    assert result is not None
    assert result["expected_property"] == expected_value
    assert validate_result_quality(result)

    # Cleanup
    cleanup_test_environment()
```

### Bug Fix Testing
```python
# Every bug fix must have regression tests
def test_bug_fix_regression():
    """Test that bug fix doesn't introduce regressions"""
    # Test the specific bug scenario
    result = scenario_that_caused_bug()
    assert result["fixed_behavior"] == expected_result

    # Test that normal functionality still works
    result = normal_scenario()
    assert result["normal_behavior"] == expected_result
```

### Performance Testing
```python
# Performance-sensitive changes need benchmarks
def test_performance_impact():
    """Test performance impact of changes"""
    baseline = measure_baseline_performance()
    current = measure_current_performance()

    # Performance should not degrade by more than 10%
    performance_change = (current - baseline) / baseline
    assert performance_change < 0.1  # 10% threshold
```

## Common Patterns

### Model Integration Pattern
```python
# When adding new models
class NewModelIntegration:
    """Integration pattern for new AI models"""

    def __init__(self, model_name: str, config: Dict):
        self.model_name = model_name
        self.config = config
        self.model = None

    def load_model(self) -> None:
        """Load model with proper error handling"""
        try:
            self.model = load_pretrained_model(self.model_name)
            logger.info(f"Successfully loaded {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load {self.model_name}: {e}")
            raise ModelLoadError(f"Cannot load model: {e}")

    def validate_model(self) -> bool:
        """Validate model functionality"""
        test_input = self._get_test_input()
        output = self.model.generate(test_input)
        return self._validate_output(output)
```

### Configuration Management Pattern
```python
# When adding configuration options
class ConfigManager:
    """Pattern for configuration management"""

    @staticmethod
    def load_config(config_path: str) -> Dict:
        """Load and validate configuration"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        return ConfigManager._validate_config(config)

    @staticmethod
    def _validate_config(config: Dict) -> Dict:
        """Validate configuration parameters"""
        required_fields = ['model', 'inference', 'modes']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")

        return config
```

### Logging Pattern
```python
# Consistent logging across the codebase
import logging

logger = logging.getLogger(__name__)

def example_function(param: str) -> str:
    """Example function with proper logging"""
    logger.info(f"Starting example_function with param: {param}")

    try:
        result = process_parameter(param)
        logger.debug(f"Processing completed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in example_function: {e}", exc_info=True)
        raise

    finally:
        logger.info("Finished example_function")
```

## Security Guidelines

### Code Security
- Never commit API keys, passwords, or secrets
- Use environment variables for sensitive configuration
- Validate all user inputs
- Use parameterized queries for any database operations
- Follow principle of least privilege for permissions

### Model Security
- Only use models from trusted sources
- Validate model checksums when downloading
- Implement proper access controls for model endpoints
- Log model access for audit trails

### Container Security
- Use official base images when possible
- Run containers as non-root users
- Scan images for vulnerabilities
- Minimize container capabilities

## Keywords <!-- #keywords -->
- contributing guide
- development setup
- code style
- commit format
- pull request process
- testing requirements
- security guidelines
- Docker development
- Python conventions
- AI model integration
- HuMo contribution
- video generation development
- PyTorch development
- Gradio contribution
- container security
- performance testing
- documentation standards