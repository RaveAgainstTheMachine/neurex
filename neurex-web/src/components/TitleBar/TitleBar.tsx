import React from "react";
import { useStore } from "../../lib/store";
import { MenuBar } from "../MenuBar/MenuBar";
import "./TitleBar.css";

export function TitleBar() {
  const { activeFile } = useStore();
  const projectName = "Neurex";

  return (
    <div className="title-bar">
      <div className="title-bar__left">
        <div className="title-bar__logo">⬡</div>
        <MenuBar />
      </div>
      
      <div className="title-bar__center">
        {activeFile ? `${activeFile.split("/").pop()} — ${projectName}` : projectName}
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
