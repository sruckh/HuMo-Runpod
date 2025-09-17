# HuMo Project Conventions

## Code Style
- **Language**: Python 3.11
- **Naming**: snake_case for functions and variables, PascalCase for classes
- **Docstrings**: Comprehensive docstrings for all public methods
- **Type Hints**: Use type hints for better code maintainability
- **Error Handling**: Graceful error handling with informative messages

## File Organization
- **Scripts**: Place utility scripts in `scripts/` directory
- **Documentation**: Use markdown files with consistent naming
- **Configuration**: Environment variables for secrets, config files for parameters
- **Tests**: Place tests in `tests/` directory (to be implemented)

## Security Practices
- **Secrets**: Never commit API keys or credentials
- **Environment**: Use `.env` files for local development
- **Git**: Comprehensive `.gitignore` for sensitive files
- **Validation**: Input validation for all user inputs

## Documentation Standards
- **CLAUDE.md**: Primary guidance for Claude Code
- **CONDUCTOR.md**: Project documentation index
- **ARCHITECTURE.md**: System architecture and design decisions
- **CONTRIBUTING.md**: Development guidelines and contribution process
- **PLAYBOOKS/**: Operational procedures and deployment guides

## Version Control
- **Branching**: Feature branches for development
- **Commits**: Clear, descriptive commit messages
- **Tags**: Version tags for releases
- **Pull Requests**: Code review before merging

## Model Management
- **Caching**: Efficient model downloading with caching
- **Validation**: Model integrity verification
- **Storage**: Organized model weight storage in `./weights/`
- **Cleanup**: Proper cleanup of temporary files

## Docker Conventions
- **Base Image**: NVIDIA CUDA for GPU support
- **Layers**: Minimal layers for efficiency
- **Entrypoint**: Proper startup scripts for runtime setup
- **Ports**: Standard port 7860 for Gradio interface

## Testing Conventions
- **Unit Tests**: Test individual components
- **Integration Tests**: Test system workflows
- **E2E Tests**: End-to-end functionality testing
- **Performance Tests**: GPU performance validation

## Deployment Conventions
- **Environment**: Development, staging, production
- **Monitoring**: Health checks and logging
- **Rollback**: Emergency rollback procedures
- **Documentation**: Clear deployment instructions