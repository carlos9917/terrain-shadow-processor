# Contributing to Terrain Shadow Processor

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, GRASS version, Python version)
- Log files if applicable

### Suggesting Features

Feature requests are welcome! Please:
- Check existing issues first
- Describe the use case
- Explain why it would be useful
- Provide examples if possible

### Pull Requests

1. **Fork the repository**

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add tests if applicable
   - Update documentation

4. **Test your changes**
   ```bash
   # Test with small dataset
   ./scripts/test_small.sh

   # Test with full dataset
   ./scripts/run_single_date.sh YYYYMMDD 2
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add feature: description"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Development Setup

### Prerequisites
- GRASS GIS 7.8+
- Python 3.8+
- Required Python packages: pandas, numpy

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/terrain-shadow-processor.git
cd terrain-shadow-processor

# Set up Python virtual environment
python -m venv venv
source venv/bin/activate
pip install pandas numpy

# Configure environment
cp env.sh.example env.sh
# Edit env.sh with your paths
```

### Running Tests
```bash
source env.sh
./scripts/test_small.sh
```

## Code Style

- Python: Follow PEP 8
- Shell scripts: Use bash, include error handling
- Comments: Explain why, not what
- Documentation: Update README.md for user-facing changes

## Project Structure

```
terrain-shadow-processor/
├── src/              # Python source code
├── scripts/          # Shell scripts
├── config/           # Configuration files
├── docs/             # Documentation (if separate from markdown)
└── tests/            # Test files (future)
```

## Areas for Contribution

We welcome contributions in:

- **Performance optimization** - Faster processing algorithms
- **Documentation** - Improve guides, add examples
- **Testing** - Unit tests, integration tests
- **Features** - New shadow calculation methods, output formats
- **Bug fixes** - Fix issues, improve error handling
- **Platform support** - Windows, macOS compatibility

## Questions?

- Open an issue for questions
- Check existing documentation
- Review closed issues for similar problems

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
