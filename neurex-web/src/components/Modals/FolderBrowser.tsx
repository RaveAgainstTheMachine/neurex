import React, { useState, useEffect } from 'react';
import { Folder, ChevronLeft, Home, Check } from 'lucide-react';
import { api } from '../../lib/api';
import './Modals.css';

interface FolderBrowserProps {
  isOpen: boolean;
  initialPath?: string;
  onConfirm: (path: string) => void;
  onClose: () => void;
}

export function FolderBrowser({ isOpen, initialPath = ".", onConfirm, onClose }: FolderBrowserProps) {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [parentPath, setParentPath] = useState<string | null>(null);
  const [dirs, setDirs] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadPath(initialPath);
    }
  }, [isOpen, initialPath]);

  const loadPath = async (path: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<any>(`/api/files/browse?path=${encodeURIComponent(path)}`);
      if (data.error) {
        setError(data.error);
      } else {
        setDirs(data.dirs || []);
        setCurrentPath(data.current);
        setParentPath(data.parent);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-content--large glass animate-scale" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Select Folder</h3>
          <div className="current-path-display">
            <Home size={14} />
            <span>{currentPath}</span>
          </div>
        </div>

        <div className="modal-body folder-browser-body">
          {error && <div className="modal-error">{error}</div>}
          
          <div className="folder-list">
            {parentPath && (
              <div className="folder-item folder-item--parent" onClick={() => loadPath(parentPath)}>
                <ChevronLeft size={16} />
                <span>.. (Parent Directory)</span>
              </div>
            )}
            
            {loading ? (
              <div className="folder-browser-loading">Scanning directories...</div>
            ) : (
              dirs.map(dir => (
                <div key={dir} className="folder-item" onClick={() => loadPath(`${currentPath}/${dir}`)}>
                  <Folder size={16} />
                  <span>{dir}</span>
                </div>
              ))
            )}

            {!loading && dirs.length === 0 && !error && (
              <div className="folder-browser-empty">No subdirectories found</div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn--secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn--purple btn--with-icon" onClick={() => onConfirm(currentPath)}>
            <Check size={16} />
            <span>Select This Folder</span>
          </button>
        </div>
      </div>
    </div>
  );
}
