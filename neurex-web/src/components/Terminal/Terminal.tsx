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

// Phase 1: Centralized registry for O(1) event routing
export const terminalRegistry = new Map<string, XTerm>();

// Static global listener to avoid O(N) listener overhead
if (typeof window !== "undefined") {
  window.addEventListener("terminal_write", (e: any) => {
    const { sessionId, data } = e.detail;
    const term = terminalRegistry.get(sessionId);
    if (term) {
      term.write(data);
    }
  });
}

export function Terminal({ sessionId, onInput, onResize, isActive }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef   = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const lastSizeRef = useRef({ rows: 0, cols: 0 });

  const activeConversationId = useStore(s => s.activeConversationId);
  const theme = useStore(s => s.theme);

  // Stable refs for callbacks — never stale, never trigger re-renders
  const onInputRef  = useRef(onInput);
  const onResizeRef = useRef(onResize);
  useEffect(() => { onInputRef.current  = onInput;  }, [onInput]);
  useEffect(() => { onResizeRef.current = onResize; }, [onResize]);

  // Read line height once via getState — no subscription, no re-renders
  const lineHeightRef = useRef(theme.terminal_line_height ?? 1.2);

  // Keep lineHeight and accent color in sync without re-rendering
  useEffect(() => {
    // 1. Subscribe specifically to line_height
    const subLh = useStore.subscribe(
      (s) => s.theme.terminal_line_height,
      (lh) => {
        const val = lh ?? 1.2;
        if (val !== lineHeightRef.current && xtermRef.current) {
          lineHeightRef.current = val;
          xtermRef.current.options.lineHeight = val;
          fitAddonRef.current?.fit();
        }
      }
    );

    // 2. Subscribe specifically to accent_color
    const subAccent = useStore.subscribe(
      (s) => s.theme.accent_color,
      (accent) => {
        if (xtermRef.current && accent) {
          xtermRef.current.options.theme = {
            ...xtermRef.current.options.theme,
            cursor: accent,
            cursorAccent: "#050507",
            magenta: accent,
            selectionBackground: `${accent}44`
          };
        }
      }
    );

    return () => {
      subLh();
      subAccent();
    };
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

  // Sync terminal options when theme changes
  useEffect(() => {
    if (!xtermRef.current) return;
    const theme = useStore.getState().theme;
    xtermRef.current.options.fontSize = theme.terminal_font_size;
    xtermRef.current.options.fontFamily = theme.terminal_font_family;
    xtermRef.current.options.cursorStyle = theme.terminal_cursor_style;
    xtermRef.current.options.lineHeight = theme.terminal_line_height;
    xtermRef.current.options.theme = {
      ...xtermRef.current.options.theme,
      cursor: theme.accent_color,
      selectionBackground: `${theme.accent_color}44`,
      magenta: theme.accent_color
    };
    // Re-fit after font changes
    fitAddonRef.current?.fit();
  }, [isActive, theme.terminal_font_size, theme.terminal_font_family, theme.terminal_cursor_style, theme.terminal_line_height, theme.accent_color]);

  // Mount once per sessionId
  useEffect(() => {
    if (!terminalRef.current) return;

    const term = new XTerm({
      cursorBlink: false, // CSS managed
      allowTransparency: true,
      scrollback: 5000,
      theme: {
        background: "transparent",
        foreground: "#e8e8f0",
        cursor: useStore.getState().theme.accent_color || "hsl(260, 90%, 70%)",
        cursorAccent: "#050507",
        selectionBackground: `${useStore.getState().theme.accent_color || "hsl(260, 90%, 70%)"}44`,
        black: "#0d0d0f",
        red: "hsl(0, 85%, 65%)",
        green: "hsl(145, 80%, 50%)",
        yellow: "hsl(45, 95%, 60%)",
        blue: "hsl(215, 100%, 65%)",
        magenta: useStore.getState().theme.accent_color || "hsl(260, 90%, 70%)",
        cyan: "hsl(185, 85%, 55%)",
        white: "#e8e8f0",
      },
      fontFamily: theme.terminal_font_family,
      fontSize: theme.terminal_font_size,
      cursorStyle: theme.terminal_cursor_style,
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
    
    // Register for global event routing
    terminalRegistry.set(sessionId, term);

    const doFit = () => {
      if (!terminalRef.current || !xtermRef.current || !fitAddonRef.current) return;
      try {
        const term = xtermRef.current;
        const fitAddon = fitAddonRef.current;
        const isAtBottom = term.buffer.active.viewportY === term.buffer.active.baseY;
        fitAddon.fit();
        const { rows, cols } = term;
        if (rows > 0 && cols > 0 && (rows !== lastSizeRef.current.rows || cols !== lastSizeRef.current.cols)) {
          lastSizeRef.current = { rows, cols };
          onResizeRef.current(rows, cols);
        }
        if (isAtBottom || lastSizeRef.current.rows === 0) {
          term.scrollToBottom();
        }
      } catch (_) {}
    };

    let rafId: number = 0;
    const observer = new ResizeObserver(() => {
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(doFit);
    });
    observer.observe(terminalRef.current);

    // Phase 2: Direct DOM focus management
    const ta = term.textarea;
    const container = terminalRef.current;
    if (ta && container) {
      ta.addEventListener('focus', () => container.classList.add('is-focused'));
      ta.addEventListener('blur', () => container.classList.remove('is-focused'));
    }

    term.onData((data) => {
      const ws = (window as any).neurexWS;
      if (ws && ws.send) {
        ws.send({ type: "terminal_input", sessionId, data });
      } else {
        onInputRef.current(data);
      }
    });
    
    term.focus();
    
    // Stabilize layout and then sync history
    setTimeout(() => {
      if (!xtermRef.current) return;
      doFit();
      xtermRef.current.refresh(0, xtermRef.current.rows - 1);
      
      const ws = (window as any).neurexWS;
      if (ws && ws.send) {
        ws.send({ type: "terminal_sync", sessionId });
      }
    }, 150);

    return () => {
      cancelAnimationFrame(rafId);
      observer.disconnect();
      terminalRegistry.delete(sessionId);
      term.dispose();
      xtermRef.current  = null;
      fitAddonRef.current = null;
    };
  }, [sessionId]);

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
