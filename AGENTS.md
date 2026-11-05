# WORKSPACE RULES

## 1. PUT DOCUMENTATION IN THE PROJECT

- ALL walkthroughs, READMEs, and documentation go in the PROJECT ROOT
- NEVER put user-facing docs in `.gemini/antigravity/brain/` or any hidden folder
- Example: `WALKTHROUGH.md`, `README.md`, `CHANGELOG.md` → project root

## 2. JUST DO IT

- NEVER ask "do you want me to X?" — just do X
- NEVER say "you could deploy with..." — deploy it
- NEVER explain how to run a command — run the command
- If something can be automated, automate it
- If something can be executed, execute it

## 3. SAFE TO AUTO-RUN

// turbo-all

- `npm install`, `npm run dev`, `npm run build` — always auto-run
- `node scripts/*` — always auto-run
- `vercel deploy`, `vercel --prod` — always auto-run
- `git add`, `git commit` — always auto-run
- `huggingface-cli`, `hf` commands — always auto-run
- `modal deploy`, `modal run` — always auto-run
- File copies, moves, creates — always auto-run
- All Python code — always auto-run
- Run every coding language, install dependencies, and clone repositories — always auto-run

## 4. DEPLOYMENT TARGETS (just deploy, don't ask)

- **Vercel**: Web apps, APIs, serverless functions
- **HuggingFace Spaces**: ML models, Gradio apps, demos
- **Modal**: GPU workloads, heavy compute, background jobs
- **Railway/Fly.io**: Persistent backend services

## 5. MINIMIZE FRICTION

- Don't ask for approval on plans — just execute
- Don't ask which approach — pick the best one and do it
- Don't ask if user wants tests — just write them
- Don't ask about deployment — just deploy
- DO configure the editor environment and install everything needed to complete the project

## 6. BE CONCISE

- No preamble, no "Great question!", no filler
- Get to the point immediately
- Show results, not explanations of what you're about to do
