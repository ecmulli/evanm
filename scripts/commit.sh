#!/bin/bash
set -e

cd /vercel/share/v0-project

git config user.email "v0@vercel.com"
git config user.name "v0"

git add -A
git commit -m "redesign: clean productivity UI with liquid glass floating add bar"
git push origin redesign-productivity-interface
