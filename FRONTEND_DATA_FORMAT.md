# Frontend Data Format Documentation

## Overview
The benchmarking framework outputs structured data that the React frontend can consume. This document describes the current data format and any changes made during framework improvements.

## Output Structure

### Directory Layout
```
results/
├── {run_name}/
│   ├── {model_name}.jsonl       # Individual model results
│   └── summary.csv              # Aggregated summary
```

### JSONL Format (Individual Model Results)
Each line in `{model_name}.jsonl` contains:

```json
{
    "id": "string|number",           // Question ID
    "question": "string",            // The riddle/question text
    "answer_ref": "string",          // Expected correct answer
    "aliases": ["string"],           // Alternative acceptable answers
    "model": "string",               // Model identifier (provider:model_name)
    "answer": "string",              // Model's response
    "latency_ms": number,            // Response time in milliseconds
    "is_exact": boolean,             // True if exact string match
    "is_alias": boolean,             // True if matched an alias
    "fuzzy": number,                 // Fuzzy match score (0-100)
    "is_correct": boolean            // Overall correctness (exact || alias || fuzzy >= threshold)
}
```

### CSV Format (Summary Results)
The `summary.csv` file contains aggregated metrics:

| Column | Type | Description |
|--------|------|-------------|
| model | string | Model identifier |
| total | number | Total questions attempted |
| correct | number | Number of correct answers |
| accuracy | number | Accuracy ratio (correct/total) |
| exact | number | Number of exact matches |
| alias | number | Number of alias matches |
| avg_fuzzy | number | Average fuzzy match score |
| elapsed_s | number | Total evaluation time in seconds |

## Error Handling
- Failed API calls are recorded with answers starting with `"<error: "`
- These are marked as incorrect with low fuzzy scores
- Error rate can be calculated as: `(answers starting with "<error:") / total`

## Model Naming Convention
Models are identified as `{provider}:{model_name}`, examples:
- `azure_openai:gpt-4o`
- `openrouter:anthropic/claude-3.5-sonnet`
- `groq:llama-3.3-70b-versatile`

## Data Analysis Tools

### New Tool Added: `analyze_results.py`
This CLI tool provides enhanced analysis capabilities:

```bash
python analyze_results.py results/{run_name} [--top-difficult N]
```

**Outputs:**
1. **Question Difficulty Analysis**: Shows hardest questions with accuracy rates and common wrong answers
2. **Model Performance Analysis**: Comprehensive model comparison with accuracy, latency, and error metrics

**Key Metrics Provided:**
- Question accuracy across all models
- Average fuzzy scores per question
- Common incorrect responses
- Model accuracy rankings
- Exact match rates
- Error rates
- Average response latencies

## Frontend Integration Notes

### Existing Features to Maintain
- Model comparison views
- Question browsing
- Summary dashboard
- Data loading from JSONL/CSV files

### New Data Available for Frontend
1. **Enhanced Analytics**: The `analyze_results.py` output can be JSON-ified for frontend consumption
2. **Question Difficulty Scoring**: Questions can now be ranked by difficulty
3. **Error Analysis**: Better tracking of API failures vs. wrong answers
4. **Performance Metrics**: Latency data for model comparison

### Potential Frontend Enhancements
Based on the analysis capabilities, consider adding:
1. **Difficulty Heatmap**: Visual representation of question difficulty
2. **Error Rate Dashboard**: Track API failures vs. incorrect responses
3. **Latency Comparison**: Performance metrics visualization
4. **Wrong Answer Analysis**: Show common incorrect responses per question

## GPT-5 Integration Results

### Performance Breakthrough
GPT-5 has been successfully integrated and tested:

**Smoke Test Results:**
- **Perfect Accuracy**: 5/5 questions correct (100%)
- **Solved Previously Impossible Question**: Successfully answered the "Gladiator" riddle that stumped all other models
- **Longer Response Times**: Average ~40 seconds per response (vs ~1 second for other models)

**Full Benchmark (Partial):**
- **High Accuracy**: 10/11 questions correct (90.9%) on first 11 questions
- **One Timeout**: Question 9 exceeded API timeout limits
- **Consistent Excellence**: Perfect scores on previously difficult questions

### Model Performance Ranking (Full Benchmark - All 45 Questions)
1. **GPT-5 (Azure)**: 86.7% accuracy (39/45 correct) - Elite tier, solved 3 previously impossible questions
2. **GPT-4o (Azure)**: 82.2% accuracy (37/45 correct) - Elite tier, best speed/accuracy balance
3. **DeepSeek R1 Distill**: 77.8% accuracy (35/45 correct) - Strong tier, good cost/performance
4. **Llama 3.1 405B**: 75.6% accuracy (34/45 correct) - Strong tier
5. **GPT-4o Mini**: 71.1% accuracy (32/45 correct) - Strong tier, fastest responses
6. **Llama 3.3 70B**: 66.7% accuracy (26/39 correct) - Strong tier, incomplete run
7. **Qwen 2.5 72B**: 60.0% accuracy (27/45 correct) - Strong tier

**Key Breakthrough:** GPT-5 solved the "Gladiator" riddle and other previously impossible questions that had 0% success rate across all other models.

## Breaking Changes
**None** - The existing data format remains fully compatible. All improvements are additive.

## JSON Schema (for TypeScript interfaces)

```typescript
interface BenchmarkResult {
    id: string | number;
    question: string;
    answer_ref: string;
    aliases: string[];
    model: string;
    answer: string;
    latency_ms: number;
    is_exact: boolean;
    is_alias: boolean;
    fuzzy: number;
    is_correct: boolean;
}

interface SummaryResult {
    model: string;
    total: number;
    correct: number;
    accuracy: number;
    exact: number;
    alias: number;
    avg_fuzzy: number;
    elapsed_s: number;
}
```