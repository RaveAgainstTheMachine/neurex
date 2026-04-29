import { useState, useEffect, useRef } from "react";
import { useStore } from "../../lib/store";
import { Check, ChevronRight, Menu } from "lucide-react";
import "./MenuBar.css";

interface MenuOption {
  label?: string;
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

interface MenuBarProps {
  mode?: "vertical" | "horizontal";
}

export function MenuBar({ mode = "horizontal" }: MenuBarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<string[]>(["File"]);
  const [activeSubmenu, setActiveSubmenu] = useState<string | null>(null);
  const { 
    logout, saveFile, activeFile, setTheme, theme, 
    addTerminalSession, closeTerminalSession, activeTerminalId, 
    clearActiveTerminal, runActiveFile, setModalOpen, refreshFileTree 
  } = useStore();
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setActiveSection(null);
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
        { label: "Open File...", shortcut: "Ctrl+O" },
        { separator: true },
        { label: "Save", shortcut: "Ctrl+S", action: () => activeFile && saveFile(activeFile) },
        { label: "Save All", shortcut: "Ctrl+K S" },
        { separator: true },
        { label: "Refresh Explorer", action: refreshFileTree },
        { separator: true },
        { label: "Settings", shortcut: "Ctrl+,", action: () => setModalOpen(true) },
        { separator: true },
        { label: "Exit", action: logout }
      ]
    },
    {
      title: "Edit",
      options: [
        { label: "Undo", shortcut: "Ctrl+Z" },
        { label: "Redo", shortcut: "Ctrl+Shift+Z" },
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
      title: "View",
      options: [
        { label: "Appearance", submenu: [
          { label: "Toggle Glassmorphism", checked: theme.enable_glassmorphism, action: () => setTheme({ enable_glassmorphism: !theme.enable_glassmorphism }) },
          { label: "Toggle Animations", checked: theme.enable_animations, action: () => setTheme({ enable_animations: !theme.enable_animations }) },
          { label: "Swarm Glow", checked: theme.enable_swarm_glow, action: () => setTheme({ enable_swarm_glow: !theme.enable_swarm_glow }) }
        ]},
        { separator: true },
        { label: "Explorer", shortcut: "Ctrl+Shift+E" },
        { label: "Search", shortcut: "Ctrl+Shift+F" },
        { label: "Source Control", shortcut: "Ctrl+Shift+G" },
        { label: "Terminal", shortcut: "Ctrl+`" }
      ]
    },
    {
      title: "Terminal",
      options: [
        { label: "New Terminal", shortcut: "Ctrl+Shift+`", action: () => addTerminalSession() },
        { label: "Split Terminal", shortcut: "Ctrl+Shift+5" },
        { separator: true },
        { label: "Run Active File", shortcut: "F5" },
        { separator: true },
        { label: "Clear Terminal", shortcut: "Ctrl+L", action: clearActiveTerminal },
        { label: "Kill Terminal", action: () => closeTerminalSession(activeTerminalId) }
      ]
    },
    {
      title: "Help",
      options: [
        { label: "Welcome", action: () => window.open("https://github.com/frosty-hq/neurex", "_blank") },
        { label: "Documentation", action: () => window.open("https://github.com/frosty-hq/neurex/wiki", "_blank") },
        { label: "Show All Commands", shortcut: "Ctrl+Shift+P" },
        { separator: true },
        { label: "Check for Updates..." },
        { separator: true },
        { label: "About Neurex" }
      ]
    }
  ];

  const renderOptions = (options: MenuOption[], onSelect: () => void) => (
    <div className="menu-options">
      {options.map((opt, i) => (
        opt.separator ? (
          <div key={i} className="menu-separator" />
        ) : (
          <div key={i} className="menu-option-wrapper">
            <button
              className={`menu-option ${opt.submenu ? "has-submenu" : ""}`}
              onClick={() => {
                if (!opt.submenu) {
                  opt.action?.();
                  onSelect();
                } else {
                  setActiveSubmenu(activeSubmenu === opt.label ? null : (opt.label || null));
                }
              }}
            >
              <div className="menu-option__left">
                <div className="check-placeholder">
                  {opt.checked && <Check size={12} />}
                </div>
                <span>{opt.label}</span>
              </div>
              {opt.shortcut && <span className="menu-shortcut">{opt.shortcut}</span>}
              {opt.submenu && <ChevronRight size={12} className="submenu-chevron" />}
            </button>

            {opt.submenu && activeSubmenu === opt.label && (
              <div className="menu-submenu">
                {opt.submenu.map((sub, j) => (
                  <button
                    key={j}
                    className="menu-option"
                    onClick={() => {
                      sub.action?.();
                      onSelect();
                    }}
                  >
                    <div className="menu-option__left">
                      <div className="check-placeholder">
                        {sub.checked && <Check size={12} />}
                      </div>
                      <span>{sub.label}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )
      ))}
    </div>
  );

  return (
    <div className="menu-bar" ref={menuRef}>
      <button 
        className={`burger-trigger ${isOpen ? "active" : ""}`}
        onClick={() => {
          setIsOpen(!isOpen);
          setActiveSection(null);
        }}
        title="Main Menu"
      >
        <Menu size={22} />
      </button>

      {isOpen && mode === "vertical" && (
        <div className="menu-drawer animate-slide-right">
          <div className="menu-drawer__header">
            <Menu size={16} />
            <span>NEUREX</span>
          </div>
          <div className="menu-drawer__content">
            {menus.map(section => (
              <div key={section.title} className={`menu-section ${expandedSections.includes(section.title) ? "expanded" : ""}`}>
                <button 
                  className="menu-section__header"
                  onClick={() => setExpandedSections(prev => prev.includes(section.title) ? [] : [section.title])}
                  onMouseEnter={() => {
                    if (expandedSections.length > 0) {
                      setExpandedSections([section.title]);
                    }
                  }}
                >
                  <div className="chevron-icon">›</div>
                  <span>{section.title}</span>
                </button>
                {expandedSections.includes(section.title) && renderOptions(section.options, () => setIsOpen(false))}
              </div>
            ))}
          </div>
        </div>
      )}

      {isOpen && mode === "horizontal" && (
        <div className="menu-horizontal-bar animate-slide-down">
          {menus.map(section => (
            <div key={section.title} className="menu-horizontal-item">
              <button 
                className={`menu-horizontal-btn ${activeSection === section.title ? "active" : ""}`}
                onClick={() => setActiveSection(activeSection === section.title ? null : section.title)}
                onMouseEnter={() => {
                  if (activeSection) {
                    setActiveSection(section.title);
                  }
                }}
              >
                {section.title}
              </button>
              {activeSection === section.title && (
                <div className="menu-horizontal-dropdown animate-fade-in">
                   {renderOptions(section.options, () => { setIsOpen(false); setActiveSection(null); })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
