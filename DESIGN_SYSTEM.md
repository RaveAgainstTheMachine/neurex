# Neurex UI/UX Design Language

## 🌓 Core Philosophy: "The Ghost in the Machine"
Neurex is designed to feel like a high-performance, sentient operating system. It avoids generic flat design in favor of **Depth**, **Translucency**, and **Kinetic Motion**.

## 🎨 Color Palette (The Void)
- **Background (Obsidian)**: `#09090b` (Deep, pure black for OLED contrast)
- **Panel (Void)**: `hsla(240, 10%, 4%, 0.7)` (Semi-transparent with backdrop-blur)
- **Accent (Neurex Purple)**: `hsl(260, 90%, 70%)` (A vibrant, glowing purple)
- **Status (Plasma)**: 
  - Success: `hsl(150, 80%, 60%)`
  - Error: `hsl(0, 80%, 60%)`
  - Warning: `hsl(35, 90%, 60%)`

## 🧱 Visual Elements
### 1. Glassmorphism
- All panels must use `backdrop-filter: blur(12px)`.
- Borders should be subtle: `1px solid hsla(0, 0%, 100%, 0.1)`.
- Avoid solid backgrounds; let the "plasma" underlays shine through.

### 2. Kinetic Motion
- Transitions should use `cubic-bezier(0.4, 0, 0.2, 1)` for a "heavy" but responsive feel.
- Loading states should be **continuous**, never jerky. Use CSS transitions on the `width` property for progress bars.
- Micro-interactions: Hover states should use subtle scale increases (`1.02x`) and bloom effects.

### 3. Typography
- **Primary**: `Inter`, `Outfit`, or `Roboto` (Clean, modern sans-serif).
- **Monospace**: `JetBrains Mono` or `Fira Code` (For code and system readouts).
- **Hierarchy**: Use wide letter-spacing (`0.1em`) for headers and metadata to evoke a "terminal" feel.

## 🕹️ Interaction Principles
- **No Placeholders**: Never use generic icons if a high-fidelity one is available.
- **Immediate Feedback**: Every action should trigger a visual change (toast, pulse, or state shift).
- **Persistence**: The UI state (open files, scroll positions) must survive refreshes.

## 🌌 Splash Screen (The Handshake)
The splash screen is the "Boot Sequence". It must feel like the AI is initializing.
- **Accurate Progress**: The bar must represent the actual WebSocket handshake and data scan.
- **Shimmer**: Use linear gradients that move to simulate "data flowing".

### 4. Infrastructure & Metrics
- **Origin Badges**: Use distinct, desaturated color capsules for model origins (LOCAL: Gray, HF: Blue, MESH: Purple).
- **Metric Gauges**: Resource usage (RAM/VRAM) should be displayed as percentage bars with a "pulsing" glow that intensifies as usage approaches 90%.
- **Skill Toggles**: Use custom-styled checkboxes that transform into glowing indicators when active.
