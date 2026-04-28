// src/components/ContextMenu/ContextMenu.tsx
import React, { useEffect, useState, useCallback } from 'react';
import './ContextMenu.css';

interface ContextMenuItem {
  label: string;
  icon?: React.ReactNode;
  action: () => void;
  danger?: boolean;
}

interface ContextMenuProps {
  items: ContextMenuItem[];
  targetSelector: string;
}

export function ContextMenu({ items, targetSelector }: ContextMenuProps) {
  const [visible, setVisible] = useState(false);
  const [pos, setPos] = useState({ x: 0, y: 0 });

  const handleContext = useCallback((e: MouseEvent) => {
    const target = e.target as HTMLElement;
    if (target.closest(targetSelector)) {
      e.preventDefault();
      setPos({ x: e.clientX, y: e.clientY });
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

  return (
    <div 
      className="context-menu" 
      style={{ top: pos.y, left: pos.x }}
      onClick={(e) => e.stopPropagation()}
    >
      {items.map((item, i) => (
        <div 
          key={i} 
          className={`context-menu__item ${item.danger ? 'danger' : ''}`}
          onClick={() => {
            item.action();
            setVisible(false);
          }}
        >
          {item.icon && <span className="context-menu__icon">{item.icon}</span>}
          <span className="context-menu__label">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
