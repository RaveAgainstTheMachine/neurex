// src/components/Terminal/Terminal.tsx
"use client";

import { useEffect, useRef } from "react";
import { Terminal as XTerm } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { WebLinksAddon } from "@xterm/addon-web-links";
import "@xterm/xterm/css/xterm.css";
import "./Terminal.css";

interface TerminalProps {
  sessionId: string;
  onInput: (data: string) => void;
  onResize: (rows: number, cols: number) => void;
}

export function Terminal({ sessionId, onInput, onResize }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);

  useEffect(() => {
    if (!terminalRef.current) return;

    const term = new XTerm({
      cursorBlink: true,
      allowTransparency: true,
      scrollback: 5000,
      rows: 24,
      lineHeight: 1.4,
      allowProposedApi: true,
      theme: {
        background: "#050507",
        foreground: "#e8e8f0",
        cursor: "hsl(240, 6%, 45%)",
        selectionBackground: "rgba(255, 255, 255, 0.1)",
        black: "#0d0d0f",
        red: "hsl(0, 85%, 65%)",
        green: "hsl(145, 80%, 50%)",
        yellow: "hsl(45, 95%, 60%)",
        blue: "hsl(215, 100%, 65%)",
        magenta: "hsl(260, 90%, 70%)",
        cyan: "hsl(185, 85%, 55%)",
        white: "#e8e8f0",
      },
      fontFamily: "var(--font-mono)",
      fontSize: 12,
      convertEol: true
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.loadAddon(new WebLinksAddon());

    term.open(terminalRef.current);

    const doFit = () => {
      try {
        fitAddon.fit();
        onResize(term.rows, term.cols);
      } catch (e) {}
    };

    // Initial fit
    setTimeout(doFit, 100);

    const observer = new ResizeObserver(() => {
      doFit();
    });
    observer.observe(terminalRef.current);

    term.onData((data) => {
      onInput(data);
    });

    xtermRef.current = term;

    // Listen for writes specific to THIS session
    const handleWrite = (e: any) => {
      if (e.detail.sessionId === sessionId) {
        const term = xtermRef.current;
        if (term) {
          term.write(e.detail.data);
          term.scrollToBottom();
        }
      }
    };
    window.addEventListener("terminal_write", handleWrite);
    
    // Force focus
    term.focus();

    return () => {
      observer.disconnect();
      window.removeEventListener("terminal_write", handleWrite);
      term.dispose();
    };
  }, [sessionId]); // Re-init when sessionId changes

  return <div ref={terminalRef} className="terminal-container" />;
}

export const terminalEvents = {
  write: (sessionId: string, data: string) => {
    const event = new CustomEvent("terminal_write", { 
      detail: { sessionId, data } 
    });
    window.dispatchEvent(event);
  }
};
