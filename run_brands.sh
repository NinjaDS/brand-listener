#!/bin/bash
cd /Users/kumaresaperumal/Ideas/brand-listener
source venv/bin/activate
echo "=== Curlsmith ==="
python run_suite.py --brand "Curlsmith"
echo ""
echo "=== Lands End ==="
python run_suite.py --brand "Lands' End"
