// src/components/ContextMenu/ContextMenu.tsx
import React, { useEffect, useState, useCallback } from 'react';
import './ContextMenu.css';

interface ContextMenuItem {
  label?: string;
  icon?: React.ReactNode;
  action?: (target: HTMLElement) => void;
  danger?: boolean;
  shortcut?: string;
  type?: 'separator' | 'item';
  visible?: (target: HTMLElement) => boolean;
}

interface ContextMenuProps {
  items: ContextMenuItem[];
  targetSelector: string;
}

export function ContextMenu({ items, targetSelector }: ContextMenuProps) {
  const [visible, setVisible] = useState(false);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [targetElement, setTargetElement] = useState<HTMLElement | null>(null);

  const handleContext = useCallback((e: MouseEvent) => {
    const target = e.target as HTMLElement;
    const matched = target.closest(targetSelector) as HTMLElement;
    if (matched) {
      e.preventDefault();
      setPos({ x: e.clientX, y: e.clientY });
      setTargetElement(matched);
      setVisible(true);
    } else {
      setVisible(false);
    }
  }, [targetSelector]);

  const handleClick = useCallback(() => setVisible(false), []);

  useEffect(() => {
    window.addEventListener('contextmenu', handleContext);
    window.addEventListener('click', handleClick);
    return () => {
      window.removeEventListener('contextmenu', handleContext);
      window.removeEventListener('click', handleClick);
    };
  }, [handleContext, handleClick]);

  if (!visible) return null;

  const filteredItems = items.filter(item => {
    if (!item.visible) return true;
    if (!targetElement) return false;
    return item.visible(targetElement);
  });

  return (
    <div 
      className="context-menu" 
      style={{ top: pos.y, left: pos.x }}
      onClick={(e) => e.stopPropagation()}
    >
      {filteredItems.map((item, i) => (
        item.type === 'separator' ? (
          <div key={i} className="context-menu__separator" />
        ) : (
          <div 
            key={i} 
            className={`context-menu__item ${item.danger ? 'danger' : ''}`}
            onClick={() => {
              if (item.action && targetElement) item.action(targetElement);
              setVisible(false);
            }}
          >
            <div className="context-menu__item-left">
              {item.icon && <span className="context-menu__icon">{item.icon}</span>}
              <span className="context-menu__label">{item.label}</span>
            </div>
            {item.shortcut && <span className="context-menu__shortcut">{item.shortcut}</span>}
          </div>
        )
      ))}
    </div>
  );
}
