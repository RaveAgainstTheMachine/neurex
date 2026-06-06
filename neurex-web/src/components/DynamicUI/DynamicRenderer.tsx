/**
 * components/DynamicUI/DynamicRenderer.tsx
 * Neural UI Generation (Phase 42).
 * Renders JSON-based 'Blueprints' into functional, glassmorphic UI components.
 */
import React from 'react';

export interface UIElement {
  type: 'card' | 'metric' | 'button' | 'text' | 'group';
  id: string;
  label?: string;
  value?: string | number;
  action?: string;
  children?: UIElement[];
  style?: React.CSSProperties;
}

export interface UIBlueprint {
  id: string;
  title: string;
  layout: UIElement[];
}

const DynamicElement: React.FC<{ element: UIElement }> = ({ element }) => {
  const baseStyles = "transition-all duration-300 ease-in-out";
  
  switch (element.type) {
    case 'group':
      return (
        <div id={element.id} className={`${baseStyles} flex flex-wrap gap-4`} style={element.style}>
          {element.children?.map(child => <DynamicElement key={child.id} element={child} />)}
        </div>
      );
    case 'card':
      return (
        <div id={element.id} className={`${baseStyles} bg-void/50 backdrop-blur-lg border border-white/10 rounded-xl p-4 shadow-xl`} style={element.style}>
          {element.label && <h4 className="text-xs uppercase tracking-widest text-white/50 mb-2">{element.label}</h4>}
          {element.children?.map(child => <DynamicElement key={child.id} element={child} />)}
        </div>
      );
    case 'metric':
      return (
        <div id={element.id} className={`${baseStyles} flex flex-col`} style={element.style}>
          <span className="text-2xl font-bold text-neurex-purple glow-sm">{element.value}</span>
          <span className="text-[10px] text-white/40 uppercase tracking-tighter">{element.label}</span>
        </div>
      );
    case 'button':
      return (
        <button 
          id={element.id}
          className={`${baseStyles} px-4 py-2 bg-neurex-purple/20 border border-neurex-purple/50 rounded-lg text-xs hover:bg-neurex-purple/40 active:scale-95`}
          onClick={() => console.log(`Dynamic Action: ${element.action}`)}
          style={element.style}
        >
          {element.label}
        </button>
      );
    case 'text':
      return <p id={element.id} className="text-sm text-white/80" style={element.style}>{element.value}</p>;
    default:
      return null;
  }
};

export const DynamicRenderer: React.FC<{ blueprint: UIBlueprint | null }> = ({ blueprint }) => {
  if (!blueprint) return null;

  return (
    <div className="dynamic-ui-container p-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <header className="mb-6">
        <h2 className="text-lg font-light tracking-widest uppercase text-white flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-neurex-purple animate-pulse" />
          {blueprint.title}
        </h2>
      </header>
      <div className="flex flex-col gap-6">
        {blueprint.layout.map(element => <DynamicElement key={element.id} element={element} />)}
      </div>
    </div>
  );
};
