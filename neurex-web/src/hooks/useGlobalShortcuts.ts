import { useEffect } from "react";
import { useStore } from "../lib/store";

interface ShortcutActions {
  setPaletteMode: (mode: "none" | "language" | "indent" | "encoding" | "global") => void;
  setSidebarTab: (tab: any) => void;
  setShowAIPanel: (val: boolean | ((v: boolean) => boolean)) => void;
}

export function useGlobalShortcuts({ setPaletteMode, setSidebarTab, setShowAIPanel }: ShortcutActions) {
  const { 
    activeFile, saveFile, addTerminalSession, 
    clearActiveTerminal, runActiveFile, setModalOpen 
  } = useStore();

  useEffect(() => {
    const handleGlobalKey = (e: KeyboardEvent) => {
      // Command Palette
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "P") {
        e.preventDefault();
        setPaletteMode("global");
      }
      // Global Search
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "F") {
        e.preventDefault();
        setSidebarTab("search");
      }
      // Save File
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        if (activeFile) {
          saveFile(activeFile);
        }
      }
      // Settings
      if ((e.metaKey || e.ctrlKey) && e.key === ",") {
        e.preventDefault();
        setModalOpen(true);
      }
      // New Terminal
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "`") {
        e.preventDefault();
        addTerminalSession();
      }
      // Clear Terminal
      if ((e.metaKey || e.ctrlKey) && e.key === "l") {
        e.preventDefault();
        clearActiveTerminal();
      }
      // Pin/Unpin Tab
      if (e.altKey && e.key === "p") {
        e.preventDefault();
        if (activeFile) useStore.getState().togglePin(activeFile);
      }
      // Go to File (Quick Open)
      if ((e.metaKey || e.ctrlKey) && e.key === "p" && !e.shiftKey && !e.altKey) {
        e.preventDefault();
        // Trigger global search or a specific quick-open event
        window.dispatchEvent(new CustomEvent('open_quick_open'));
      }
      // Toggle AI Panel
      if ((e.metaKey || e.ctrlKey) && e.key === "L") {
        e.preventDefault();
        setShowAIPanel(prev => !prev);
      }
      // Run Active File
      if (e.key === "F5") {
        e.preventDefault();
        runActiveFile();
      }
    };

    window.addEventListener("keydown", handleGlobalKey);
    return () => window.removeEventListener("keydown", handleGlobalKey);
  }, [
    activeFile, saveFile, addTerminalSession, clearActiveTerminal, 
    runActiveFile, setModalOpen, setPaletteMode, setSidebarTab, setShowAIPanel
  ]);
}
