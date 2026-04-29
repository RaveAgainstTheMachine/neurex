// src/components/Terminal/Terminal.tsx
"use client";

import { useEffect, useRef } from "react";
import { Terminal as XTerm } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { WebLinksAddon } from "@xterm/addon-web-links";
import "@xterm/xterm/css/xterm.css";
import "./Terminal.css";
import { useStore } from "../../lib/store";

interface TerminalProps {
  sessionId: string;
  onInput: (data: string) => void;
  onResize: (rows: number, cols: number) => void;
  isActive?: boolean;
}

export function Terminal({ sessionId, onInput, onResize, isActive }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef   = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const lastSizeRef = useRef({ rows: 0, cols: 0 });

  // Stable refs for callbacks — never stale, never trigger re-renders
  const onInputRef  = useRef(onInput);
  const onResizeRef = useRef(onResize);
  useEffect(() => { onInputRef.current  = onInput;  }, [onInput]);
  useEffect(() => { onResizeRef.current = onResize; }, [onResize]);

  // Read line height once via getState — no subscription, no re-renders
  const lineHeightRef = useRef(useStore.getState().theme.terminal_line_height ?? 1.2);

  // Keep lineHeight in sync without re-rendering
  useEffect(() => {
    return useStore.subscribe(
      (state) => {
        const lh = state.theme.terminal_line_height ?? 1.2;
        if (lh !== lineHeightRef.current) {
          lineHeightRef.current = lh;
          if (xtermRef.current) {
            xtermRef.current.options.lineHeight = lh;
            fitAddonRef.current?.fit();
          }
        }
      }
    );
  }, []);

  // isActive: re-fit + focus without destroying anything
  useEffect(() => {
    if (!isActive || !xtermRef.current) return;
    const t = setTimeout(() => {
      fitAddonRef.current?.fit();
      xtermRef.current?.scrollToBottom();
      xtermRef.current?.focus();
    }, 50);
    return () => clearTimeout(t);
  }, [isActive]);

  // Mount once per sessionId
  useEffect(() => {
    if (!terminalRef.current) return;

    const term = new XTerm({
      cursorBlink: true,
      cursorStyle: "block",
      allowTransparency: true,
      scrollback: 5000,
      theme: {
        background: "#050507",
        foreground: "#e8e8f0",
        cursor: "hsl(260, 90%, 70%)",
        selectionBackground: "rgba(139, 92, 246, 0.3)",
        black: "#0d0d0f",
        red: "hsl(0, 85%, 65%)",
        green: "hsl(145, 80%, 50%)",
        yellow: "hsl(45, 95%, 60%)",
        blue: "hsl(215, 100%, 65%)",
        magenta: "hsl(260, 90%, 70%)",
        cyan: "hsl(185, 85%, 55%)",
        white: "#e8e8f0",
      },
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      fontSize: 13,
      lineHeight: lineHeightRef.current,
      allowProposedApi: true,
      convertEol: true,
      scrollOnUserInput: true,
    });

    const fitAddon = new FitAddon();
    fitAddonRef.current = fitAddon;
    term.loadAddon(fitAddon);
    term.loadAddon(new WebLinksAddon());

    term.open(terminalRef.current);
    xtermRef.current = term;

    const doFit = () => {
      if (!terminalRef.current || !xtermRef.current || !fitAddonRef.current) return;
      try {
        const isAtBottom = xtermRef.current.buffer.active.viewportY === xtermRef.current.buffer.active.baseY;
        fitAddonRef.current.fit();
        
        const { rows, cols } = xtermRef.current;
        if (rows > 0 && cols > 0 && (rows !== lastSizeRef.current.rows || cols !== lastSizeRef.current.cols)) {
          lastSizeRef.current = { rows, cols };
          onResizeRef.current(rows, cols);
        }
        
        if (isAtBottom) {
          xtermRef.current.scrollToBottom();
        }
      } catch (_) {}
    };

    let resizeTimer: any;
    const observer = new ResizeObserver(() => {
      // Return to immediate fit — we'll handle stutter by optimizing the internal doFit logic
      doFit();
    });
    observer.observe(terminalRef.current);

    // Route keystrokes to PTY unconditionally bypassing React closures
    term.onData((data) => {
      const ws = (window as any).neurexWS;
      if (ws && ws.send) {
        ws.send({ type: "terminal_input", sessionId, data });
      } else {
        onInputRef.current(data); // Fallback to prop
      }
    });
    
    // Fallback: intercept keys directly if onData misses them (rare but possible in some electron/iframe envs)
    term.onKey(({ key, domEvent }) => {
      if (term.options.disableStdin) return;
      // We don't want to double-send, so we rely on onData, 
      // but keeping this hook in case we need to debug or intercept.
    });

    const handleWrite = (e: any) => {
      if (e.detail.sessionId === sessionId) {
        term.write(e.detail.data, () => term.scrollToBottom());
      }
    };
    window.addEventListener("terminal_write", handleWrite);

    term.focus();

    return () => {
      clearTimeout(resizeTimer);
      observer.disconnect();
      window.removeEventListener("terminal_write", handleWrite);
      term.dispose();
      xtermRef.current  = null;
      fitAddonRef.current = null;
    };
  }, [sessionId]); // mount once per session — nothing else

  return (
    <div
      ref={terminalRef}
      className="terminal-container"
      onClick={() => xtermRef.current?.focus()}
      style={{ height: "100%", width: "100%", background: "#050507", outline: "none" }}
      tabIndex={-1}
    />
  );
}

export const terminalEvents = {
  write: (sessionId: string, data: string) => {
    window.dispatchEvent(new CustomEvent("terminal_write", { detail: { sessionId, data } }));
  },
};
