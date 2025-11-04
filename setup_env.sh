#!/bin/bash

# Setup script for Portal Base API Client
# This script helps configure the API key

echo "================================================"
echo "Portal Base API Client - Environment Setup"
echo "================================================"
echo ""

# Check if Secrets file exists
if [ -f "Secrets" ]; then
    echo "✅ Secrets file already exists"
else
    echo "📝 Creating Secrets file..."
    echo ""
    echo "Please enter your Base.gov.pt API key:"
    read -r api_key
    
    if [ -z "$api_key" ]; then
        echo "❌ No API key provided. Exiting."
        exit 1
    fi
    
    echo "BASE_API_KEY:\"$api_key\"" > Secrets
    echo "✅ Secrets file created successfully!"
fi

echo ""
echo "================================================"
echo "Installing Python dependencies..."
echo "================================================"
pip3 install -r requirements.txt

echo ""
echo "================================================"
echo "✅ Setup complete!"
echo "================================================"
echo ""
echo "You can now run:"
echo "  • streamlit run app.py          (Web application)"
echo "  • python3 get_date.py 31/10/2025  (Command line)"
echo ""

