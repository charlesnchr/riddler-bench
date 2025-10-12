# Riddler Bench

A lightweight evaluation harness for testing LLMs on deliberately oblique, riddle-like information retrieval questions. Instead of asking "What movie has hobbits?", we ask "A tale of circular jewelry and walking, where the shortest carry the greatest burden." This tests lateral thinking and the ability to connect abstract clues to concrete knowledge.

<div align="center">
<img src="assets/ai-robot-examines-egyptian-scrolls.png" alt="AI Robot Examining Ancient Scrolls" width="250">
</div>


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
> "Manager who prefers wearable tech for surveillance"
>
> Answer: *Sauron*

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
- [ ] **Fix question detail mismatch bug**: Questions in the hardest question table sometimes display incorrect model responses when clicked. The overview shows which models were correct, but scrolling down reveals responses that don't match the original question. This appears to be a data registration issue when multiple datasets are loaded simultaneously.
- [ ] **Clean reasoning traces before correctness evaluation**: Models that output reasoning in `<think></think>` tags can get incorrectly marked as correct when the reasoning trace happens to contain the answer. The correctness checker should strip reasoning traces first, similar to how we separate reasoning/output tokens for DeepSeek and Qwen models.

## License

MIT
