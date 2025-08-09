#!/bin/bash
set -e

# Colors for output
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
PURPLE=$'\033[0;35m'
NC=$'\033[0m' # No Color

# Default values
DATASET=""
RUN_TYPE=""
OUTPUT_DIR=""
MODELS=""
AZURE_WORKERS=8
GROQ_WORKERS=2
OPENROUTER_WORKERS=5
CONFIG_FILE="config/models.yaml"
TEMPERATURE=0.0
FUZZY_THRESHOLD=85

# Help function
show_help() {
    cat << EOF
${BLUE}Riddler Bench - Benchmark Runner${NC}

Usage: $0 [smoke|full] [OPTIONS]

${YELLOW}Arguments:${NC}
  smoke          Run smoke test (5 questions) for quick validation
  full           Run full benchmark (100 questions) for comprehensive evaluation

${YELLOW}Options:${NC}
  -m, --models MODEL_LIST    Comma-separated list of models (e.g. "azure_openai:gpt-5,azure_openai:gpt-4o")
                            If not specified, runs all configured models
  -o, --output DIR          Output directory (default: results/[timestamp]-[type])
  -c, --config FILE         Config file path (default: config/models.yaml)
  --azure-workers N         Number of parallel workers for Azure models (default: 8)
  --groq-workers N          Number of parallel workers for Groq models (default: 2)
  --openrouter-workers N    Number of parallel workers for OpenRouter models (default: 5)
  --temperature TEMP        Model temperature (default: 0.0)
  --fuzzy-threshold N       Fuzzy match threshold 0-100 (default: 85)
  -h, --help               Show this help message

${YELLOW}Examples:${NC}
  # Quick smoke test with all models
  $0 smoke

  # Full benchmark with specific models
  $0 full --models "azure_openai:gpt-5,azure_openai:o3-pro"

  # Smoke test with custom workers
  $0 smoke --azure-workers 10 --groq-workers 1

  # Full benchmark with custom output directory
  $0 full --output results/my-comprehensive-test

EOF
}

# Parse command line arguments
if [[ $# -eq 0 ]] || [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Check if first argument is run type
if [[ "$1" == "smoke" ]] || [[ "$1" == "full" ]]; then
    RUN_TYPE="$1"
    shift
else
    echo -e "${RED}Error: First argument must be 'smoke' or 'full'${NC}"
    echo "Run '$0 --help' for usage information."
    exit 1
fi

# Parse remaining arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--models)
            MODELS="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --azure-workers)
            AZURE_WORKERS="$2"
            shift 2
            ;;
        --groq-workers)
            GROQ_WORKERS="$2"
            shift 2
            ;;
        --openrouter-workers)
            OPENROUTER_WORKERS="$2"
            shift 2
            ;;
        --temperature)
            TEMPERATURE="$2"
            shift 2
            ;;
        --fuzzy-threshold)
            FUZZY_THRESHOLD="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            echo "Run '$0 --help' for usage information."
            exit 1
            ;;
    esac
done

# Set dataset based on run type
if [[ "$RUN_TYPE" == "smoke" ]]; then
    DATASET="data/smoke.jsonl"
    DEFAULT_OUTPUT_PREFIX="smoke"
else
    DATASET="data/benchmark_oblique_harder.jsonl"
    DEFAULT_OUTPUT_PREFIX="full"
fi

# Set default output directory if not specified
if [[ -z "$OUTPUT_DIR" ]]; then
    TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
    OUTPUT_DIR="results/${TIMESTAMP}-${DEFAULT_OUTPUT_PREFIX}"
fi

# Validate inputs
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo -e "${RED}Error: Config file '$CONFIG_FILE' not found${NC}"
    exit 1
fi

if [[ ! -f "$DATASET" ]]; then
    echo -e "${RED}Error: Dataset file '$DATASET' not found${NC}"
    exit 1
fi

# Check environment setup
if [[ ! -f ".env" ]]; then
    echo -e "${YELLOW}Warning: .env file not found. Run 'python setup_env.py' to configure API keys.${NC}"
fi

# Display configuration
echo -e "${BLUE}🚀 Riddler Bench - Starting ${RUN_TYPE} evaluation${NC}"
echo -e "${PURPLE}Configuration:${NC}"
echo -e "  Dataset: ${DATASET}"
echo -e "  Output: ${OUTPUT_DIR}"
echo -e "  Config: ${CONFIG_FILE}"
if [[ -n "$MODELS" ]]; then
    echo -e "  Models: ${MODELS}"
else
    echo -e "  Models: All configured models"
fi
echo -e "  Workers: Azure=${AZURE_WORKERS}, Groq=${GROQ_WORKERS}, OpenRouter=${OPENROUTER_WORKERS}"
echo -e "  Temperature: ${TEMPERATURE}"
echo -e "  Fuzzy threshold: ${FUZZY_THRESHOLD}"
echo ""

# Ask for confirmation on full runs
if [[ "$RUN_TYPE" == "full" ]]; then
    echo -e "${YELLOW}⚠️  Full benchmark will run 100 questions on all models. This may take time and cost money.${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Cancelled.${NC}"
        exit 0
    fi
fi

# Build command
CMD="uv run riddler-bench eval-parallel"
CMD="$CMD --dataset \"$DATASET\""
CMD="$CMD --config \"$CONFIG_FILE\""
CMD="$CMD --out \"$OUTPUT_DIR\""
CMD="$CMD --azure-workers $AZURE_WORKERS"
CMD="$CMD --groq-workers $GROQ_WORKERS"
CMD="$CMD --openrouter-workers $OPENROUTER_WORKERS"
CMD="$CMD --temperature $TEMPERATURE"
CMD="$CMD --fuzzy-threshold $FUZZY_THRESHOLD"

if [[ -n "$MODELS" ]]; then
    CMD="$CMD --models \"$MODELS\""
fi

# Show command being run
echo -e "${GREEN}Executing:${NC} $CMD"
echo ""

# Run the command
eval $CMD

# Check if command succeeded
if [[ $? -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✅ Benchmark completed successfully!${NC}"
    echo -e "${BLUE}Results saved to: ${OUTPUT_DIR}${NC}"
    echo ""
    echo -e "${PURPLE}Next steps:${NC}"
    echo -e "  • Analyze results: ${GREEN}python analyze_results.py \"$OUTPUT_DIR\"${NC}"
    echo -e "  • View summary: ${GREEN}uv run riddler-bench score --results \"$OUTPUT_DIR\"${NC}"
    if [[ "$RUN_TYPE" == "smoke" ]]; then
        echo -e "  • Run full benchmark: ${GREEN}$0 full${NC}"
    fi
else
    echo ""
    echo -e "${RED}❌ Benchmark failed. Check the output above for errors.${NC}"
    exit 1
fi
