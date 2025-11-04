"""
Configuration management for Portal Base API Client

Loads API key from Streamlit secrets, environment variables, or Secrets file.
Priority: Streamlit secrets > Environment variable > Secrets file
"""

import os


def get_api_key():
    """
    Get the API key from Streamlit secrets, environment variable, or Secrets file.
    
    Returns:
        str: The API key
        
    Raises:
        ValueError: If API key is not found
    """
    # Try Streamlit secrets first (for Streamlit Cloud deployments)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'BASE_API_KEY' in st.secrets:
            return st.secrets['BASE_API_KEY']
    except (ImportError, FileNotFoundError, KeyError):
        pass
    
    # Try environment variable
    api_key = os.environ.get('BASE_API_KEY')
    
    if api_key:
        return api_key
    
    # Try reading from Secrets file (for local development)
    secrets_file = os.path.join(os.path.dirname(__file__), 'Secrets')
    if os.path.exists(secrets_file):
        try:
            with open(secrets_file, 'r') as f:
                content = f.read().strip()
                # Handle format: BASE_API_KEY:"value" or BASE_API_KEY:value
                if ':' in content:
                    api_key = content.split(':', 1)[1].strip().strip('"')
                    return api_key
        except Exception as e:
            pass
    
    # If not found, raise error
    raise ValueError(
        "API key not found! Please set BASE_API_KEY in Streamlit secrets (for cloud) "
        "or as environment variable or create a Secrets file with: BASE_API_KEY:\"your_key_here\""
    )


# For convenience, expose the API key
try:
    BASE_API_KEY = get_api_key()
except ValueError:
    BASE_API_KEY = None
    print("⚠️  Warning: API key not configured. Please set BASE_API_KEY environment variable or create Secrets file.")

