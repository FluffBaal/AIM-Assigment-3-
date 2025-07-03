#!/bin/bash

# Script to fix the default branch setting
# This requires GitHub CLI to be authenticated

echo "Fix Default Branch Script"
echo "========================"
echo ""
echo "This script will change the default branch from 'feature/project-setup' to 'main'"
echo ""
echo "Prerequisites:"
echo "1. GitHub CLI must be installed"
echo "2. You must be authenticated with GitHub CLI"
echo ""
echo "To authenticate GitHub CLI, run:"
echo "  gh auth login"
echo ""
echo "After authentication, run:"
echo "  gh repo edit FluffBaal/AIM-Assigment-3- --default-branch main"
echo ""
echo "Alternatively, you can fix this manually:"
echo "1. Go to https://github.com/FluffBaal/AIM-Assigment-3-/settings"
echo "2. Under 'Default branch', click the switch branch button"
echo "3. Select 'main' from the dropdown"
echo "4. Click 'Update'"
echo ""
echo "Current default branch status:"
git remote show origin | grep "HEAD branch"