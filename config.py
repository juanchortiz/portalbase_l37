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
                for line in f:
                    line = line.strip()
                    if line.startswith('BASE_API_KEY'):
                        if ':' in line:
                            api_key = line.split(':', 1)[1].strip().strip('"')
                            if api_key:
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


def get_hubspot_token():
    """
    Get HubSpot API token from environment variable or Secrets file.
    
    Returns:
        str: The HubSpot API token
        
    Raises:
        ValueError: If token is not found
    """
    # Try environment variable first
    token = os.environ.get('HUBSPOT_API_TOKEN')
    if token:
        return token
    
    # Try reading from Secrets file (for local development)
    secrets_file = os.path.join(os.path.dirname(__file__), 'Secrets')
    if os.path.exists(secrets_file):
        try:
            with open(secrets_file, 'r') as f:
                content = f.read().strip()
                # Handle format: HUBSPOT_API_TOKEN:"value" or HUBSPOT_API_TOKEN:value
                for line in content.split('\n'):
                    if line.strip().startswith('HUBSPOT_API_TOKEN'):
                        if ':' in line:
                            token = line.split(':', 1)[1].strip().strip('"')
                            if token:
                                return token
        except Exception:
            pass
    
    # Try Streamlit secrets (for cloud deployments)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'HUBSPOT_API_TOKEN' in st.secrets:
            return st.secrets['HUBSPOT_API_TOKEN']
    except (ImportError, FileNotFoundError, KeyError):
        pass
    
    raise ValueError(
        "HubSpot API token not found! Please set HUBSPOT_API_TOKEN environment variable "
        "or add it to Secrets file as: HUBSPOT_API_TOKEN:\"your_token_here\""
    )

