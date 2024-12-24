#!/bin/bash
cd /home/ubuntu/afe/app
source venv/bin/activate
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi
python3 main.py