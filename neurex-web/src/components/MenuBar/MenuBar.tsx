import { useState, useEffect, useRef } from "react";
import { useStore } from "../../lib/store";
import { Check, ChevronRight } from "lucide-react";
import "./MenuBar.css";
import { NeurexLogo } from "../Icons/NeurexLogo";

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
  const { logout, saveFile, activeFile, setTheme, theme } = useStore();
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
        { separator: true },
        { label: "Auto Save", checked: true },
        { separator: true },
        { label: "Exit", action: logout }
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
        { label: "Paste", shortcut: "Ctrl+V" }
      ]
    },
    {
      title: "View",
      options: [
        { label: "Appearance", submenu: [
          { label: "Toggle Glassmorphism", checked: theme.enable_glassmorphism, action: () => setTheme({ enable_glassmorphism: !theme.enable_glassmorphism }) },
          { label: "Toggle Animations", checked: theme.enable_animations, action: () => setTheme({ enable_animations: !theme.enable_animations }) }
        ]},
        { separator: true },
        { label: "Explorer", shortcut: "Ctrl+Shift+E" },
        { label: "Search", shortcut: "Ctrl+Shift+F" },
        { label: "Terminal", shortcut: "Ctrl+`" }
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
        className={`burger-trigger logo-trigger ${isOpen ? "active" : ""}`}
        onClick={() => {
          setIsOpen(!isOpen);
          setActiveSection(null);
        }}
        title="Neurex Main Menu"
      >
        <NeurexLogo size={22} className="neurex-logo-svg" />
      </button>

      {isOpen && mode === "vertical" && (
        <div className="menu-drawer animate-slide-right">
          <div className="menu-drawer__header">
            <NeurexLogo size={18} />
            <span>NEUREX TREE</span>
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
