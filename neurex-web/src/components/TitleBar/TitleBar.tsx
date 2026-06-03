import React from "react";
import { useStore } from "../../lib/store";
import { MenuBar } from "../MenuBar/MenuBar";
import "./TitleBar.css";

export function TitleBar() {
  const { activeFile, workspaceFolders, openFiles } = useStore();
  const projectName = "Neurex";

  const titleText = React.useMemo(() => {
    const workspaceName = workspaceFolders.length > 1 
      ? "Workspace" 
      : (workspaceFolders[0]?.split("/").pop() || projectName);
    
    if (!activeFile) return workspaceName;
    
    const file = openFiles.find(f => f.path === activeFile);
    const fileName = activeFile.split("/").pop();
    const folderName = file?.root ? file.root.split("/").pop() : workspaceName;
    
    return `${fileName} — ${folderName}`;
  }, [activeFile, workspaceFolders, openFiles]);

  React.useEffect(() => {
    document.title = `${titleText} - ${projectName}`;
  }, [titleText]);

  return (
    <div className="title-bar">
      <div className="title-bar__left">
        <div className="title-bar__logo">⬡</div>
        <MenuBar />
      </div>
      
      <div className="title-bar__center">
        {titleText}
      </div>
      
      <div className="title-bar__right">
        <div className="window-controls">
          <div className="window-control">─</div>
          <div className="window-control">☐</div>
          <div className="window-control window-control--close">✕</div>
        </div>
      </div>
    </div>
  );
}
