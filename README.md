# HelpfulBatBot 🦇

An intelligent Q&A bot for the Underworld3 geodynamics modeling framework, powered by Claude AI and semantic search.

## What It Does

HelpfulBatBot indexes Underworld3 documentation, examples, and tests to answer user questions with context-aware responses. It uses:
- **FAISS** for fast semantic search
- **Sentence Transformers** for document embeddings
- **Claude AI** with prompt caching for intelligent answers
- **Multi-repository support** via git integration

## Quick Start

### Local Development

```bash
# Clone this repository
git clone https://github.com/underworldcode/underworld-helpful-batbot.git
cd underworld-helpful-batbot

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the bot (will clone UW3 content on first run)
python HelpfulBat_app.py
```

### Ask Questions

```bash
# In another terminal
python ask.py "How do I create a mesh in Underworld3?"
python ask.py "What are swarms?"
python ask.py status
```

## How It Works

### Multi-Repository Indexing

The bot automatically clones and indexes content from configured git repositories:

```yaml
# content_sources.yaml
content_sources:
  - name: "underworld3"
    url: "https://github.com/underworldcode/underworld3.git"
    branch: "main"
    local_path: "./content_cache/underworld3"
    update_frequency: "daily"
    include_paths:
      - "docs/beginner/tutorials/*.ipynb"
      - "examples/*.py"
      - "tests/test_0[0-6]*.py"
```

### Content Updates

- **On startup**: Checks if content needs updating based on `update_frequency`
- **Cached locally**: Cloned repos stored in `./content_cache/`
- **Shallow clones**: Fast downloads with `--depth 1`
- **Automatic pulls**: Updates existing content without re-cloning

### What Gets Indexed

From the Underworld3 repository (~86 files):
- ✅ Beginner tutorials
- ✅ Example scripts
- ✅ A/B grade test files
- ✅ Main documentation (README, CLAUDE.md)
- ❌ Source code internals (excluded)
- ❌ Developer documentation (excluded)

## Configuration

### Environment Variables (.env)

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (defaults shown)
CLAUDE_MODEL=claude-3-haiku-20240307
CONTENT_UPDATE_FREQUENCY=daily
PORT=8001
```

### Content Sources (content_sources.yaml)

See `content_sources.yaml` for full configuration. You can add multiple repositories:

```yaml
content_sources:
  - name: "underworld3"
    # ... config ...

  - name: "community-examples"
    url: "https://github.com/yourorg/uw3-examples.git"
    # ... config ...
```

## Deployment

### Fly.io (Recommended)

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Create app (Sydney region)
flyctl launch --name underworld-helpfulbat --region syd

# Create persistent volume for content cache
flyctl volumes create helpfulbat_content --size 5 --region syd

# Set secrets
flyctl secrets set ANTHROPIC_API_KEY=sk-ant-...

# Deploy
flyctl deploy
```

### Docker

```bash
# Build image
docker build -t helpfulbatbot .

# Run with volume for content cache
docker run -d \
  -p 8001:8001 \
  -v helpfulbat_content:/app/content_cache \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  helpfulbatbot
```

## API Endpoints

Once running, the bot provides:

- **POST /ask** - Ask a question
- **GET /health** - Health check
- **GET /docs** - API documentation (Swagger UI)

### Example API Call

```bash
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I create a mesh?", "max_context_items": 6}'
```

## File Structure

```
underworld-helpful-batbot/
├── HelpfulBat_app.py          # Main bot server
├── content_manager.py         # Multi-repo content management
├── content_sources.yaml       # Repository configuration
├── ask.py                     # CLI client
├── start_bot.sh               # Startup script
├── demo.sh                    # Demo script
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker image
├── fly.toml                   # Fly.io configuration
├── .env.example               # Example environment config
└── content_cache/             # Cloned repositories (gitignored)
    └── underworld3/           # UW3 content
```

## Development

### Adding a New Repository

1. Edit `content_sources.yaml`:
   ```yaml
   content_sources:
     - name: "new-repo"
       url: "https://github.com/org/repo.git"
       branch: "main"
       local_path: "./content_cache/new-repo"
       update_frequency: "daily"
       include_paths:
         - "**/*.md"
       exclude_paths:
         - ".git/**/*"
   ```

2. Restart the bot - it will automatically clone and index the new repository

### Testing Content Manager

```python
from content_manager import ContentManager

# Load configuration
manager = ContentManager("content_sources.yaml")

# Force update all sources
manager.update_all(force=True)

# Get statistics
stats = manager.get_stats()
print(f"Total files: {stats['total_files']}")
```

## Cost Estimates

With Claude Haiku and prompt caching:

- **100 questions/day**: ~$25/month
- **500 questions/day**: ~$125/month
- **2000 questions/day**: ~$500/month

Hosting on Fly.io free tier: $0/month (within limits)

## Future Enhancements

### Phase 2: GitHub Integration
- Auto-respond to GitHub issues
- React to user feedback with 👍/👎
- Flag low-confidence answers for human review

### Phase 3: Web Widget
- Embedded chat widget in documentation
- Context-aware help based on page

### Phase 4: VS Code Extension
- Inline code assistance
- Syntax-aware Q&A

### Phase 5: Learning Loop
- Track user feedback
- Identify documentation gaps
- Auto-generate planning documents from user needs

## License

[Add your license here]

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Contact

- **Project**: https://github.com/underworldcode/underworld3
- **Bot Issues**: https://github.com/underworldcode/underworld-helpful-batbot/issues
- **Underworld**: https://www.underworld.org.au/
