# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow

- Commit and push to GitHub after every meaningful unit of work — do not batch multiple unrelated changes into one commit
- Use clean, descriptive commit messages that explain what changed and why
- Push frequently so work is never lost and the GitHub repo always reflects current state
- GitHub account: SinhaShambhavi — repo: https://github.com/SinhaShambhavi/tic-tac-toe

## Project Structure

This is a personal projects directory. Current contents:

- `body-composition-dashboard.html` — body composition tracking dashboard (manual entry + charts + Renpho sync)
- `renpho-sync.py` — Python backend server for Renpho API integration (proxies encrypted API calls)
- `shambhavi-studio.html` — single-page site for Shambhavi fragrance studio (implemented from a Claude Design file; open directly in a browser)
- `tictactoe.html` — self-contained single-file web game (HTML + CSS + JS, no build step)
- `hello.py`, `main.py` — scratch Python files

## Body Composition Dashboard

Open `body-composition-dashboard.html` in a browser. Renpho sync runs directly in the browser — no server or backend needed. Go to "Renpho Sync" tab, enter your Renpho credentials, and click Sync Now.

## Tic-Tac-Toe

Open `tictactoe.html` directly in a browser — no server or build step needed.
