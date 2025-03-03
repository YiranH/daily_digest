#!/bin/bash

# Exit on error
set -e

echo "Setting up the AI Daily Digest development environment..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    
    # Add Poetry to PATH
    export PATH="$HOME/.local/bin:$PATH"
    echo "export PATH=\"$HOME/.local/bin:\$PATH\"" >> ~/.profile
    echo "export PATH=\"$HOME/.local/bin:\$PATH\"" >> ~/.zshrc
    
    echo "Poetry installed successfully!"
    echo "PATH updated to include Poetry. You may need to restart your terminal or run:"
    echo "  source ~/.zshrc"
else
    echo "Poetry is already installed."
fi

# Install dependencies using Poetry (without installing the root package)
echo "Installing dependencies..."
poetry install --no-root

# Create feeds directory if it doesn't exist
mkdir -p feeds

echo "Setup complete! You can now run the scraper with:"
echo "  poetry run python -m src.main"
echo ""
echo "To set up GitHub Pages, you'll need to:"
echo "1. Push this repository to GitHub"
echo "2. Go to the repository settings"
echo "3. In the 'Pages' section, set the source to 'GitHub Actions'"
echo ""
echo "Happy coding!" 