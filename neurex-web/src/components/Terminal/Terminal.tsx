// src/components/Terminal/Terminal.tsx
import { useEffect, useRef } from "react";
import { Terminal as XTerm } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { WebLinksAddon } from "@xterm/addon-web-links";
import "@xterm/xterm/css/xterm.css";
import "./Terminal.css";

interface TerminalProps {
  onInput: (data: string) => void;
  onResize: (rows: number, cols: number) => void;
  output?: string;
}

export function Terminal({ onInput, onResize, output }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);

  useEffect(() => {
    if (!terminalRef.current) return;

    const term = new XTerm({
      cursorBlink: true,
      allowTransparency: true,
      scrollback: 1000,
      theme: {
        background: "hsl(240, 10%, 4%)",
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
      lineHeight: 1.4,
      allowProposedApi: true,
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.loadAddon(new WebLinksAddon());

    term.open(terminalRef.current);
    
    // Initial fit
    setTimeout(() => {
      fitAddon.fit();
      onResize(term.rows, term.cols);
    }, 100);

    const observer = new ResizeObserver(() => {
      fitAddon.fit();
    });
    observer.observe(terminalRef.current);

    term.onData((data) => {
      onInput(data);
    });

    term.onResize(({ rows, cols }) => {
      onResize(rows, cols);
    });

    xtermRef.current = term;

    const handleWrite = (e: any) => {
      xtermRef.current?.write(e.detail);
    };
    window.addEventListener("terminal_write", handleWrite);

    return () => {
      observer.disconnect();
      window.removeEventListener("terminal_write", handleWrite);
      term.dispose();
    };
  }, []);

  return <div ref={terminalRef} className="terminal-container" />;
}

export const terminalEvents = {
  write: (data: string) => {
    const event = new CustomEvent("terminal_write", { detail: data });
    window.dispatchEvent(event);
  }
};
