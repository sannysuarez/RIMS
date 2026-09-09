#!/bin/bash
# RIMS Reset Script Wrapper
# Quick and easy way to reset your application

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default values
ENV="development"
CREATE_ADMIN=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --prod)
            ENV="production"
            shift
            ;;
        --dev)
            ENV="development"
            shift
            ;;
        --no-admin)
            CREATE_ADMIN=false
            shift
            ;;
        --help)
            echo "RIMS Reset Script"
            echo ""
            echo "Usage: ./reset.sh [options]"
            echo ""
            echo "Options:"
            echo "  --dev              Reset development environment (default)"
            echo "  --prod             Reset production environment"
            echo "  --no-admin         Skip creating default admin user"
            echo "  --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./reset.sh                    # Reset dev, create admin"
            echo "  ./reset.sh --prod             # Reset production"
            echo "  ./reset.sh --dev --no-admin   # Reset dev, no admin user"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build python command
PYTHON_ARGS=""
if [ "$ENV" == "production" ]; then
    PYTHON_ARGS="--prod"
else
    PYTHON_ARGS="--dev"
fi

if [ "$CREATE_ADMIN" == false ]; then
    PYTHON_ARGS="$PYTHON_ARGS --no-admin"
fi

# Run the reset script
python3 reset.py $PYTHON_ARGS
