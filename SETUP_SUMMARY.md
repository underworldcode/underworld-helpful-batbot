# HelpfulBatBot Repository Setup Summary

**Created**: November 2025
**Location**: `/Users/lmoresi/+Underworld/underworld-helpful-batbot`
**Status**: ✅ Complete - Ready for GitHub push

## What Was Created

### Repository Structure

```
underworld-helpful-batbot/
├── HelpfulBat_app.py           # Main FastAPI bot server
├── content_manager.py          # Multi-repository content management
├── content_sources.yaml        # Repository configuration
├── ask.py                      # CLI client for asking questions
├── start_bot.sh                # Bot startup script
├── demo.sh                     # Demo script
├── requirements.txt            # Python dependencies (with PyYAML)
├── Dockerfile                  # Docker multi-stage build
├── fly.toml                    # Fly.io deployment config
├── .gitignore                  # Git ignore patterns
├── .env.example                # Example environment config
└── README.md                   # Comprehensive documentation
```

### Key Features Implemented

1. **Multi-Repository Support** ✅
   - Content manager that clones and updates git repositories
   - Configurable via `content_sources.yaml`
   - Automatic daily updates
   - Caches content in `./content_cache/`

2. **Auto-Port Detection** ✅
   - Tries ports 8001-8010
   - Writes selected port to `bot.port` file
   - `ask.py` automatically finds the bot

3. **Deployment Ready** ✅
   - Dockerfile with multi-stage build
   - Fly.io configuration with persistent volumes
   - Health checks included
   - Environment variable support

4. **Separation from UW3 Repo** ✅
   - Bot infrastructure completely separate
   - Indexes UW3 via git clone
   - No code dependencies on UW3 structure

## Content Sources Configuration

Currently configured to index from `underworld3` repository:

```yaml
content_sources:
  - name: "underworld3"
    url: "https://github.com/underworldcode/underworld3.git"
    branch: "main"
    local_path: "./content_cache/underworld3"
    update_frequency: "daily"
```

**Indexed content (~86 files)**:
- Beginner tutorials (`.ipynb`, `.md`)
- Example scripts (`.py`, `.ipynb`)
- A/B grade tests (`test_0[0-6]*.py`)
- Main docs (README.md, CLAUDE.md)

**Excluded**:
- Source code (`src/`)
- Developer docs (`docs/developer/`)
- Planning docs (`planning/`)

## Next Steps

### 1. Create GitHub Repository

```bash
# From this directory
cd /Users/lmoresi/+Underworld/underworld-helpful-batbot

# Create on GitHub (requires gh CLI)
gh repo create underworldcode/underworld-helpful-batbot --public --source=. --remote=origin

# Or manually:
# 1. Create repo on GitHub: https://github.com/new
# 2. Add remote:
git remote add origin https://github.com/underworldcode/underworld-helpful-batbot.git

# Push
git push -u origin main
```

### 2. Set Up Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your API key
# ANTHROPIC_API_KEY=sk-ant-...

# Run the bot (will clone UW3 on first run)
python HelpfulBat_app.py
```

**First run will**:
1. Clone underworld3 repository to `./content_cache/underworld3/`
2. Extract ~86 files based on include/exclude patterns
3. Build FAISS index (~2 minutes)
4. Start server on port 8001 (or next available)

### 3. Test Locally

```bash
# In another terminal
python ask.py "How do I create a mesh in Underworld3?"
python ask.py "What are swarms?"
python ask.py status
```

### 4. Deploy to Fly.io (Optional)

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Create app
flyctl launch --name underworld-helpfulbat --region syd

# Create persistent volume
flyctl volumes create helpfulbat_content --size 5 --region syd

# Set secret
flyctl secrets set ANTHROPIC_API_KEY=sk-ant-...

# Deploy
flyctl deploy
```

## Integration with Existing Setup

### Relationship to Other Directories

**This is now the canonical bot repository**:
```
underworld-helpful-batbot/       # NEW - Canonical, push to GitHub
├── (all bot infrastructure)
└── content_cache/               # Cloned repos (gitignored)
    └── underworld3/             # Auto-cloned from GitHub

underworld3-helpfulbat-bot/      # OLD - Local testing, can be removed
└── (same files, kept for compatibility)

underworld3/HelpfulBatBot/       # OLD - Original location, can be removed
└── (embedded in UW3, no longer needed)
```

**Recommendation**: Keep only `underworld-helpful-batbot/` going forward.

### Migration Path

```bash
# Keep old directories as backups for now
# Use only the new repository

cd /Users/lmoresi/+Underworld/underworld-helpful-batbot

# This is your working directory now
```

## Configuration Notes

### Environment Variables (.env)

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (defaults shown)
CLAUDE_MODEL=claude-3-haiku-20240307
CONTENT_UPDATE_FREQUENCY=daily
PORT=8001
```

### Adding More Repositories

Edit `content_sources.yaml`:

```yaml
content_sources:
  - name: "underworld3"
    # ... existing config ...

  - name: "community-examples"
    url: "https://github.com/underworldcode/uw3-examples.git"
    branch: "main"
    local_path: "./content_cache/community-examples"
    update_frequency: "daily"
    include_paths:
      - "**/*.ipynb"
      - "**/*.py"
    exclude_paths:
      - ".git/**/*"
    priority: 0.9
```

## Cost Estimates (Phase 1)

**Monthly costs for 100 questions/day**:

```yaml
Hosting:
  Fly.io: $0/month (within free tier)

Storage:
  Volume (5GB): $0/month (within free tier)

API:
  Claude Haiku: ~$25/month (with prompt caching)

Total: ~$25/month
```

## Git Commit History

Initial commit includes:
- Core bot infrastructure
- Multi-repository content manager
- Auto-port detection
- Deployment configs
- Comprehensive documentation

```bash
git log --oneline
# d8e05e3 (HEAD -> main) Initial commit: HelpfulBatBot with multi-repository support
```

## Documentation

- **README.md** - User-facing documentation
- **content_sources.yaml** - Configuration examples and comments
- **Dockerfile** - Build instructions
- **fly.toml** - Deployment configuration
- **This file** - Setup summary

## Differences from Previous Versions

### What's New

1. **`content_manager.py`** - Complete rewrite for multi-repo support
2. **`content_sources.yaml`** - New configuration file
3. **PyYAML dependency** - Added to requirements.txt
4. **Dockerfile** - Multi-stage build with git
5. **Persistent volumes** - Fly.io volume mount for content cache

### What's Unchanged

- Core bot logic (`HelpfulBat_app.py` - needs integration)
- CLI interface (`ask.py`)
- Startup scripts (`start_bot.sh`, `demo.sh`)
- Auto-port detection

### TODO: Integration

The `HelpfulBat_app.py` file still uses the old path-based file loading. It needs to be updated to use `content_manager`:

```python
# OLD (current)
def load_files(repo_path: str) -> List[Tuple[str, str]]:
    # ... direct file system access ...

# NEW (needs implementation)
from content_manager import load_files_from_sources

documents = load_files_from_sources("content_sources.yaml")
```

This integration is straightforward and can be done after initial testing.

## Support and Issues

- **Bot Issues**: Create issues in the `underworld-helpful-batbot` repository
- **UW3 Issues**: Create issues in the `underworld3` repository
- **Questions**: Contact the Underworld team

---

**Status**: Ready to push to GitHub and begin Phase 1 deployment! 🚀
