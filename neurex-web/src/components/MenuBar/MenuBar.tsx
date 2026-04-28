import { useState, useEffect, useRef } from "react";
import { useStore } from "../../lib/store";
import { Check } from "lucide-react";
import "./MenuBar.css";

interface MenuOption {
  label: string;
  shortcut?: string;
  action?: () => void;
  checked?: boolean;
  disabled?: boolean;
  separator?: boolean;
  submenu?: MenuOption[];
}

interface MenuSection {
  title: string;
  options: MenuOption[];
}

export function MenuBar() {
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const { logout, saveFile, activeFile, setTheme, theme } = useStore();
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setActiveMenu(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const menus: MenuSection[] = [
    {
      title: "File",
      options: [
        { label: "New Text File", shortcut: "Ctrl+N" },
        { label: "New File...", shortcut: "Ctrl+Alt+Super+N" },
        { label: "New Window", shortcut: "Ctrl+Shift+N" },
        { separator: true },
        { label: "Open File...", shortcut: "Ctrl+O" },
        { label: "Open Folder...", shortcut: "Ctrl+K Ctrl+O" },
        { label: "Open Recent", submenu: [{ label: "No Recent Folders" }] },
        { separator: true },
        { label: "Save", shortcut: "Ctrl+S", action: () => activeFile && saveFile(activeFile) },
        { label: "Save As...", shortcut: "Ctrl+Shift+S" },
        { label: "Save All" },
        { separator: true },
        { label: "Auto Save", checked: true },
        { label: "Preferences", submenu: [
            { label: "Settings", shortcut: "Ctrl+," },
            { label: "Keyboard Shortcuts" },
            { label: "Color Theme" }
          ] 
        },
        { separator: true },
        { label: "Close Editor", shortcut: "Ctrl+W" },
        { label: "Close Folder", shortcut: "Ctrl+K F" },
        { separator: true },
        { label: "Exit", shortcut: "Ctrl+Q", action: logout }
      ]
    },
    {
      title: "Edit",
      options: [
        { label: "Undo", shortcut: "Ctrl+Z" },
        { label: "Redo", shortcut: "Ctrl+Y" },
        { separator: true },
        { label: "Cut", shortcut: "Ctrl+X" },
        { label: "Copy", shortcut: "Ctrl+C" },
        { label: "Paste", shortcut: "Ctrl+V" },
        { separator: true },
        { label: "Find", shortcut: "Ctrl+F" },
        { label: "Replace", shortcut: "Ctrl+H" }
      ]
    },
    {
      title: "Selection",
      options: [
        { label: "Select All", shortcut: "Ctrl+A" },
        { label: "Expand Selection", shortcut: "Shift+Alt+Right" },
        { label: "Shrink Selection", shortcut: "Shift+Alt+Left" },
        { separator: true },
        { label: "Copy Line Up", shortcut: "Shift+Alt+Up" },
        { label: "Copy Line Down", shortcut: "Shift+Alt+Down" },
        { label: "Move Line Up", shortcut: "Alt+Up" },
        { label: "Move Line Down", shortcut: "Alt+Down" }
      ]
    },
    {
      title: "View",
      options: [
        { label: "Command Palette...", shortcut: "Ctrl+Shift+P" },
        { separator: true },
        { label: "Explorer", shortcut: "Ctrl+Shift+E" },
        { label: "Search", shortcut: "Ctrl+Shift+F" },
        { label: "Source Control", shortcut: "Ctrl+Shift+G" },
        { label: "Run", shortcut: "Ctrl+Shift+D" },
        { separator: true },
        { label: "Output", shortcut: "Ctrl+K Ctrl+H" },
        { label: "Terminal", shortcut: "Ctrl+`" },
        { separator: true },
        { label: "Word Wrap", shortcut: "Alt+Z" },
        { label: "Glassmorphism", checked: theme.enable_glassmorphism, action: () => setTheme({ enable_glassmorphism: !theme.enable_glassmorphism }) }
      ]
    },
    {
      title: "Go",
      options: [
        { label: "Back", shortcut: "Alt+Left" },
        { label: "Forward", shortcut: "Alt+Right" },
        { separator: true },
        { label: "Go to File...", shortcut: "Ctrl+P" },
        { label: "Go to Symbol...", shortcut: "Ctrl+Shift+O" }
      ]
    },
    {
      title: "Run",
      options: [
        { label: "Start Debugging", shortcut: "F5" },
        { label: "Run Without Debugging", shortcut: "Ctrl+F5" }
      ]
    },
    {
      title: "Terminal",
      options: [
        { label: "New Terminal", shortcut: "Ctrl+Shift+`" },
        { label: "Split Terminal", shortcut: "Ctrl+Shift+5" }
      ]
    },
    {
      title: "Help",
      options: [
        { label: "Welcome" },
        { label: "Documentation" },
        { label: "Release Notes" },
        { separator: true },
        { label: "About Neurex" }
      ]
    }
  ];

  return (
    <div className="menu-bar" ref={menuRef}>
      {menus.map((menu) => (
        <div key={menu.title} className="menu-item">
          <button
            className={`menu-trigger ${activeMenu === menu.title ? "active" : ""}`}
            onClick={() => setActiveMenu(activeMenu === menu.title ? null : menu.title)}
            onMouseEnter={() => activeMenu && setActiveMenu(menu.title)}
          >
            {menu.title}
          </button>
          {activeMenu === menu.title && (
            <div className="menu-dropdown animate-slide-up">
              {menu.options.map((opt, i) => (
                opt.separator ? (
                  <div key={i} className="menu-separator" />
                ) : (
                  <button
                    key={i}
                    className={`menu-option ${opt.disabled ? "disabled" : ""} ${opt.submenu ? "has-submenu" : ""}`}
                    onClick={() => {
                      opt.action?.();
                      setActiveMenu(null);
                    }}
                  >
                    <div className="menu-option__label">
                      <div className="check-mark">
                        {opt.checked && <Check size={12} />}
                      </div>
                      {opt.label}
                    </div>
                    {opt.shortcut && <span className="menu-option__shortcut">{opt.shortcut}</span>}
                  </button>
                )
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
