#!/bin/bash

# Install Playwright browsers for Streamlit Cloud
python -m pip install --upgrade pip
python -m playwright install chromium
python -m playwright install-deps chromium
