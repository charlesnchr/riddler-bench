# Riddler Bench

<img src="assets/ai-robot-examines-egyptian-scrolls.png" alt="AI Robot Examining Ancient Scrolls" width="400" align="right">

A lightweight evaluation harness for testing LLMs on deliberately oblique, riddle-like information retrieval questions.

## Quick Start

### Prerequisites
- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) package manager
- Node.js (for UI components)

### Setup
1. Clone and install:
```bash
git clone https://github.com/yourusername/riddler-bench.git
cd riddler-bench
uv sync
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run a benchmark:
```bash
uv run riddler-bench eval \
  --dataset data/benchmark.jsonl \
  --config config/models.yaml \
  --models "azure_openai:gpt-4o" \
  --out results/test-run
```

### Environment Variables
- `AZURE_OPENAI_BASE_URL` - Your Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key
- `AZURE_OPENAI_API_VERSION` - API version (e.g., "2025-04-01-preview")
- `OPENROUTER_API_KEY` - OpenRouter API key (optional)
- `GROQ_API_KEY` - Groq API key (optional)

## What It Does

This benchmark tests how well language models can solve riddles that describe real-world entities (movies, people, places, etc.) in deliberately convoluted ways. Instead of direct questions, it uses oblique clues that require lateral thinking.

Example riddle:
> "A tale of circular jewelry and walking, where the shortest carry the greatest burden"
> 
> Answer: *The Lord of the Rings*

## Features

- Support for Azure OpenAI, OpenRouter, and Groq providers
- Parallel evaluation for faster benchmarking
- Web UI for exploring results
- Fuzzy matching and alias support for answers
- Optional LLM judge for semantic scoring

## Results UI

Start the web interface to explore benchmark results:
```bash
cd results-ui
npm install
npm run dev
```

## TODO

- [ ] Add Google Gemini models to the test suite

## License

MIT