#!/bin/sh
set -e

# If no arguments are passed, show help or a status message
if [ "$#" -eq 0 ]; then
    echo "Scalable CLI Container is running."
    echo "Use 'sc --help' or pass commands to execute."
    exec sc --help
fi

# Execute the passed arguments (e.g., 'sc login' or 'sc portfolio')
exec sc "$@"