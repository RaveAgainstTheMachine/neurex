// src/components/Terminal/Terminal.tsx
"use client";

import { useEffect, useRef, useState } from "react";
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
  const [proposal, setProposal] = useState<{ command: string; taskId: string } | null>(null);
  const proposalRef = useRef<{ command: string; taskId: string } | null>(null);

  useEffect(() => {
    proposalRef.current = proposal;
  }, [proposal]);

  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef   = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const lastSizeRef = useRef({ rows: 0, cols: 0 });
  const resizeTimeoutRef = useRef<any>(null);

  const theme = useStore(s => s.theme);

  // Stable refs for callbacks — never stale, never trigger re-renders
  const onInputRef  = useRef(onInput);
  const onResizeRef = useRef(onResize);
  useEffect(() => { onInputRef.current  = onInput;  }, [onInput]);
  useEffect(() => { onResizeRef.current = onResize; }, [onResize]);

  // Read line height once via getState — no subscription, no re-renders
  const lineHeightRef = useRef(theme.terminal_line_height ?? 1.2);

  const handleApprove = () => {
    const activeProposal = proposalRef.current;
    if (!activeProposal) return;
    const send = useStore.getState().send;
    if (send) {
      send({
        type: "terminal_command_approval",
        sessionId,
        taskId: activeProposal.taskId,
        approved: true,
        command: activeProposal.command
      });
    }
    setProposal(null);
  };

  const handleDecline = () => {
    const activeProposal = proposalRef.current;
    if (!activeProposal) return;
    const send = useStore.getState().send;
    if (send) {
      send({
        type: "terminal_command_approval",
        sessionId,
        taskId: activeProposal.taskId,
        approved: false,
        command: activeProposal.command
      });
    }
    setProposal(null);
  };

  useEffect(() => {
    const handleProposal = (e: any) => {
      const { sessionId: eventSid, command, taskId } = e.detail;
      if (eventSid === sessionId) {
        setProposal({ command, taskId });
      }
    };

    window.addEventListener("neurex_command_proposal", handleProposal);
    return () => window.removeEventListener("neurex_command_proposal", handleProposal);
  }, [sessionId]);

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
        foreground: "#cccccc",
        cursor: useStore.getState().theme.accent_color || "#9c6fff",
        cursorAccent: "#050507",
        selectionBackground: `${useStore.getState().theme.accent_color || "#9c6fff"}44`,
        black: "#000000",
        red: "#cd3131",
        green: "#0dbc79",
        yellow: "#e5e510",
        blue: "#2472c8",
        magenta: "#bc3fbc",
        cyan: "#11a8cd",
        white: "#e5e5e5",
        brightBlack: "#666666",
        brightRed: "#f14c4c",
        brightGreen: "#23d18b",
        brightYellow: "#f5f543",
        brightBlue: "#3b8eea",
        brightMagenta: "#d670d6",
        brightCyan: "#29b8db",
        brightWhite: "#e5e5e5",
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
        fitAddon.fit();
        const { rows, cols } = term;
        if (rows > 0 && cols > 0 && (rows !== lastSizeRef.current.rows || cols !== lastSizeRef.current.cols)) {
          lastSizeRef.current = { rows, cols };
          if (resizeTimeoutRef.current) clearTimeout(resizeTimeoutRef.current);
          resizeTimeoutRef.current = setTimeout(() => {
            onResizeRef.current(rows, cols);
          }, 100);
        }
        // Keep cursor anchored to bottom after rendering updates
        setTimeout(() => {
          term.scrollToBottom();
        }, 10);
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
      if (proposalRef.current) {
        if (data === "\r") {
          handleApprove();
        } else if (data === "\u001b") {
          handleDecline();
        }
        return;
      }
      const send = useStore.getState().send;
      if (send) {
        send({ type: "terminal_input", sessionId, data });
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
      
      const send = useStore.getState().send;
      if (send) {
        const state = useStore.getState();
        const session = state.terminalSessions.find(s => s.id === sessionId);
        // Prefer session-specific cwd, then workspace root, then undefined (backend falls back to WORKSPACE_PATH)
        const cwd = session?.cwd || state.workspaceFolders[0] || undefined;
        send({
          type: "terminal_sync",
          sessionId,
          cwd,
          rows: xtermRef.current?.rows ?? 24,
          cols: xtermRef.current?.cols ?? 80,
        });
      }
    }, 150);

    return () => {
      cancelAnimationFrame(rafId);
      observer.disconnect();
      if (resizeTimeoutRef.current) clearTimeout(resizeTimeoutRef.current);
      terminalRegistry.delete(sessionId);
      term.dispose();
      xtermRef.current  = null;
      fitAddonRef.current = null;
    };
  }, [sessionId]);

  return (
    <div
      className={`terminal-wrapper-outer ${proposal ? "has-proposal" : ""}`}
      style={{ height: "100%", width: "100%", position: "relative" }}
    >
      <div
        ref={terminalRef}
        className="terminal-container"
        onClick={() => xtermRef.current?.focus()}
        style={{ height: "100%", width: "100%", background: "#050507", outline: "none" }}
        tabIndex={-1}
      />
      {proposal && (
        <div className="terminal-proposal-banner">
          <div className="proposal-badge">SUGGESTED COMMAND</div>
          <div className="proposal-command" title={proposal.command}>
            <code>{proposal.command}</code>
          </div>
          <div className="proposal-actions">
            <button className="btn-approve" onClick={handleApprove}>
              Approve (Enter)
            </button>
            <button className="btn-decline" onClick={handleDecline}>
              Decline (Esc)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export const terminalEvents = {
  write: (sessionId: string, data: string) => {
    window.dispatchEvent(new CustomEvent("terminal_write", { detail: { sessionId, data } }));
  },
};
