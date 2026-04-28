import { useState, useEffect, useRef } from "react";
import { useStore } from "../../lib/store";
import { Check } from "lucide-react";
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

export function MenuBar() {
  const [isOpen, setIsOpen] = useState(false);
  const [activeSubmenu, setActiveSubmenu] = useState<string | null>(null);
  const { logout, saveFile, activeFile, setTheme, theme } = useStore();
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setActiveSubmenu(null);
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

  return (
    <div className="menu-bar" ref={menuRef}>
      <button 
        className={`burger-trigger logo-trigger ${isOpen ? "active" : ""}`}
        onClick={() => setIsOpen(!isOpen)}
        title="Neurex Main Menu"
      >
        <span className="neurex-symbol">⬡</span>
      </button>

      {isOpen && (
        <div className="burger-dropdown animate-slide-up">
          {menus.map((section) => (
            <div key={section.title} className="burger-section">
              <div className="burger-section__title">{section.title}</div>
              <div className="burger-section__options">
                {section.options.map((opt, i) => (
                  opt.separator ? (
                    <div key={i} className="burger-separator" />
                  ) : (
                    <div key={i} className="burger-option-container">
                      <button
                        className={`burger-option ${opt.submenu ? "has-submenu" : ""} ${activeSubmenu === opt.label ? "active" : ""}`}
                        onMouseEnter={() => opt.submenu ? setActiveSubmenu(opt.label || null) : setActiveSubmenu(null)}
                        onClick={() => {
                          if (!opt.submenu) {
                            opt.action?.();
                            setIsOpen(false);
                          }
                        }}
                        title={opt.label}
                      >
                        <div className="burger-option__left">
                          <div className="check-placeholder">
                            {opt.checked && <Check size={12} />}
                          </div>
                          <span>{opt.label}</span>
                        </div>
                        {opt.shortcut && <span className="burger-shortcut">{opt.shortcut}</span>}
                      </button>
                      
                      {opt.submenu && activeSubmenu === opt.label && (
                        <div className="burger-submenu">
                          {opt.submenu.map((sub, j) => (
                            <button
                              key={j}
                              className="burger-option"
                              onClick={() => {
                                sub.action?.();
                                setIsOpen(false);
                                setActiveSubmenu(null);
                              }}
                              title={sub.label}
                            >
                              <div className="burger-option__left">
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
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
