# Terrain Shadow Processor

> Fast, parallel terrain shadow and horizon calculation using GRASS GIS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Efficient processing of terrain shadows and horizon angles from Digital Surface Models (DSM). Designed for meteorological applications, solar energy analysis, and road weather forecasting.

## Features

- ⚡ **Parallel Processing** - Utilizes Python multiprocessing for ~4x speedup
- 🌍 **GRASS GIS Integration** - Accurate terrain analysis using GRASS batch mode
- 📊 **Scalable** - Process thousands of stations efficiently
- 🔧 **Configurable** - Adjustable DSM resolution, scanning distance, and angles
- 📈 **Battle-tested** - Used in production for road weather station analysis

## Quick Start

### Prerequisites

- GRASS GIS 7.8 or later
- Python 3.8+
- Python packages: `pandas`, `numpy`

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/terrain-shadow-processor.git
cd terrain-shadow-processor

# Install Python dependencies
**Set up the virtual environment with `uv`**

This project uses `uv` for fast and efficient package management.

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate a virtual environment
uv venv .venv --python 3.11
source .venv/bin/activate

# Install the required Python dependencies
uv pip install -r requirements.txt
```

uv pip install pandas numpy

# Configure environment
cp env.sh env.sh.local
# Edit env.sh.local with your paths
```

### Basic Usage

```bash
# Source configuration
source env.sh.local

# Process stations from CSV file
./scripts/run_single_date.sh 20240824 4
```

**Input:** CSV file with station coordinates (UTM format)
```
easting|norting|station|county|roadsection
698255.77|6152611.61|1045|0|0
```

**Output:** Shadow horizon angles for each station
```
azimuth,horizon_height
0.000000,3.126225
11.250000,2.018167
...
```

## Documentation

- [Quick Start Guide](QUICKSTART.md)


## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contact

- Issues: [GitHub Issues](https://github.com/yourusername/terrain-shadow-processor/issues)

---

**Version:** 1.0.0 | **Status:** Production-ready
