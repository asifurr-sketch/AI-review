# AI Document Review System

Automated document review system using OpenAI GPT-5 for competitive programming problem analysis.

## Requirements

- **Python 3.13+** (required)
- OpenAI API key with GPT-5 access
- Git (for GitHub repository validation)

## Installation

### 1. Install Python 3.13

**Ubuntu/Debian (using deadsnakes PPA):**

```bash
# Add deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.13
sudo apt install python3.13 python3.13-venv python3.13-dev

# Verify installation
python3.13 --version
```

**Already have Python 3.13?**

```bash
python3.13 --version  # Should show Python 3.13.x
```

### 2. Clone Repository

```bash
git clone https://github.com/asifurr-sketch/AI-review.git
cd AI-review
```

### 3. Install Dependencies

```bash
python3.13 -m pip install openai
```

### 4. Set OpenAI API Key

```bash
# Option 1: Environment variable
export OPENAI_API_KEY="your-api-key-here"

# Option 2: Create .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

## Usage

```bash
# Full review (AI + GitHub validation)
python3.13 main.py document.txt

# AI reviews only
python3.13 main.py document.txt --ai-only

# GitHub validation only
python3.13 main.py document.txt --github-only

# Resume from specific point
python3.13 main.py document.txt --resume 15

# Single specific review
python3.13 main.py document.txt --single-review "Style Guide Compliance"

# Verbose output
python3.13 main.py document.txt --verbose
```

## GitHub Setup (Optional)

For private repository validation, set up SSH (watch youtube) :

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to SSH agent
ssh-add ~/.ssh/id_ed25519

# Add public key to GitHub
cat ~/.ssh/id_ed25519.pub
# Copy output and add to GitHub Settings > SSH Keys

# Test connection
ssh -T git@github.com
```

Public repositories work automatically without SSH setup.

## Output

Reports are saved to `reports/` directory with detailed analysis and pass/fail status for each review point.

## Author

**Md Asifur Rahman**

## Support

For issues or questions, please open an issue on GitHub.
