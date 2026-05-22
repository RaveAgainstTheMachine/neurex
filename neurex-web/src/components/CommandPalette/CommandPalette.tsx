import { useState, useEffect, useRef } from "react";
import { Search, Command } from "lucide-react";
import "./CommandPalette.css";

interface CommandItem {
  id: string;
  label: string;
  category?: string;
  action: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  items: CommandItem[];
  placeholder?: string;
}

export function CommandPalette({ isOpen, onClose, _title, items, placeholder }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const paletteRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredItems = items.filter(i => 
    i.label.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex(v => (v + 1) % filteredItems.length);
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex(v => (v - 1 + filteredItems.length) % filteredItems.length);
      }
      if (e.key === "Enter") {
        e.preventDefault();
        if (filteredItems[selectedIndex]) {
          filteredItems[selectedIndex].action();
          onClose();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, filteredItems, selectedIndex, onClose]);

  if (!isOpen) return null;

  return (
    <div className="palette-overlay" onClick={onClose}>
      <div className="palette-container animate-scale" onClick={e => e.stopPropagation()} ref={paletteRef}>
        <div className="palette-header">
          <div className="palette-search">
            <Search size={14} />
            <input 
              ref={inputRef}
              type="text" 
              value={query} 
              onChange={e => setQuery(e.target.value)}
              placeholder={placeholder || "Type a command or search..."}
            />
          </div>
        </div>
        <div className="palette-results">
          {filteredItems.map((item, index) => (
            <button
              key={item.id}
              className={`palette-item ${index === selectedIndex ? "active" : ""}`}
              onMouseEnter={() => setSelectedIndex(index)}
              onClick={() => {
                item.action();
                onClose();
              }}
            >
              <span className="palette-item__label">{item.label}</span>
              {item.category && <span className="palette-item__cat">{item.category}</span>}
            </button>
          ))}
          {filteredItems.length === 0 && (
            <div className="palette-empty">No results found</div>
          )}
        </div>
        <div className="palette-footer">
          <div className="palette-tip">
            <Command size={10} /> 
            <span>Select with Arrows, Confirm with Enter</span>
          </div>
        </div>
      </div>
    </div>
  );
}
