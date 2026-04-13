#!/bin/bash
set -e
cd /Users/kumaresaperumal/Ideas/brand-listener
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install linkdapi python-dotenv rich boto3 requests -q
echo ""
echo "Running Curlsmith..."
python run_suite.py --brand "Curlsmith"
echo "---"
echo "Running Lands End..."
python run_suite.py --brand "Lands' End"
