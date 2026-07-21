#!/bin/bash
# One-time setup for trafigura-scenario-v2. The agent's workspace needs its
# own isolated git history (so the autonomous agent's investigate/heal cycle
# doesn't create commits in your main AI-QA-POC repo history) - this script
# creates that history locally after you clone/pull.
set -e
cd "$(dirname "$0")/agent/workspace"
if [ -d .git ]; then
  echo "Workspace already initialized."
  exit 0
fi
git init -q
git add -A
git -c user.email="dev@trafigura-poc.local" -c user.name="Dev Team" commit -q -m "clean baseline"
echo "Agent workspace initialized with a clean baseline commit."
