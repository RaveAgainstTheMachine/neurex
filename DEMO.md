# Neurex Demo Status

**Current state**: Neurex is **not demo-ready**. Core features work in isolation, but no complete user flow has been validated end-to-end by a human.

## What the Demo Must Show (When Ready)

Once the blocking items below are resolved, we will record a continuous, unedited demo showing:

1. Opening Neurex in a browser.
2. Loading a workspace.
3. Chatting with an agent.
4. The agent proposing a file edit.
5. A human approving the edit.
6. The file appearing updated in the Monaco editor.

## Prerequisites Before Recording

1. All Tier 1 features must work together without manual intervention or backend restarts.
2. A human developer must complete the 6-step flow above at least once successfully before recording begins.

## Recording Instructions

1. Use a standard screen recording tool (or Chrome DevTools protocol for automated recording).
2. Save the output as a `.webm` file.
3. Place the file at `/assets/demo.webm` in this repository.
4. Embed the video in `README.md` under the "## Demo" section.

## Current Blocking Items

- The end-to-end flow from frontend WebSocket to backend agent execution to file modification has not been holistically verified.
- The UI for human-in-the-loop approval needs manual validation.
