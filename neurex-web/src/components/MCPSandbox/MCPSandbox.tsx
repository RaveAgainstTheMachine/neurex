import { useState, useEffect, useMemo } from "react";
import { 
  Shield, Server, Terminal, Play, AlertTriangle, RefreshCw, Plus
} from "lucide-react";
import { api } from "../../lib/api";
import toast from "react-hot-toast";
import "./MCPSandbox.css";

interface ToolParameter {
  type: string;
  description?: string;
}

interface ToolSchema {
  name: string;
  description: string;
  inputSchema: {
    type: string;
    properties: Record<string, ToolParameter>;
    required?: string[];
  };
  rule: "allow" | "ask" | "deny";
}

interface MCPServer {
  id: string;
  name: string;
  status: "connected" | "disconnected";
  type: "core" | "skill";
  tools: ToolSchema[];
}

export function MCPSandbox() {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [importUrl, setImportUrl] = useState("");
  const [importing, setImporting] = useState(false);
  const [activeServerId, setActiveServerId] = useState<string | null>(null);
  const [activeToolName, setActiveToolName] = useState<string | null>(null);
  
  // Playground state
  const [playgroundArgs, setPlaygroundArgs] = useState<Record<string, any>>({});
  const [playgroundOutput, setPlaygroundOutput] = useState<{
    status: "idle" | "running" | "success" | "error";
    result?: any;
    error?: string;
  }>({ status: "idle" });

  const fetchServers = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const data = await api.get<MCPServer[]>("/api/mcp/servers");
      if (Array.isArray(data)) {
        setServers(data);
        if (data.length > 0 && !activeServerId) {
          setActiveServerId(data[0].id);
        }
      }
    } catch (err: any) {
      toast.error(`Failed to fetch MCP servers: ${err.message || err}`);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchServers();
  }, []);

  const handleUpdatePermission = async (toolName: string, rule: "allow" | "ask" | "deny") => {
    const previousServers = [...servers];
    
    // Optimistic UI update
    setServers(prev => prev.map(server => ({
      ...server,
      tools: server.tools.map(tool => 
        tool.name === toolName ? { ...tool, rule } : tool
      )
    })));

    try {
      await api.post("/api/mcp/permissions", { tool_name: toolName, rule });
      toast.success(`Permission updated for ${toolName}`);
    } catch (err: any) {
      setServers(previousServers);
      toast.error(`Failed to update permission: ${err.message || err}`);
    }
  };

  const handleImportServer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importUrl.trim()) return;

    setImporting(true);
    const toastId = toast.loading("Importing MCP skill server...");
    try {
      await api.post("/api/mcp/servers/import", { url: importUrl });
      toast.success("MCP skill server imported successfully!", { id: toastId });
      setImportUrl("");
      fetchServers(true);
    } catch (err: any) {
      toast.error(`Import failed: ${err.message || err}`, { id: toastId });
    } finally {
      setImporting(false);
    }
  };

  const handleRunPlayground = async (toolName: string) => {
    setPlaygroundOutput({ status: "running" });
    try {
      const payload = {
        tool_name: toolName,
        arguments: playgroundArgs
      };
      const response: any = await api.post("/api/mcp/playground/run", payload);
      if (response && response.status === "success") {
        setPlaygroundOutput({ status: "success", result: response.result });
        toast.success(`Executed ${toolName} successfully`);
      } else {
        setPlaygroundOutput({ status: "error", error: response.detail || "Execution failed" });
      }
    } catch (err: any) {
      setPlaygroundOutput({ status: "error", error: err.message || String(err) });
      toast.error(`Playground execution failed: ${err.message || err}`);
    }
  };

  const activeServer = useMemo(() => {
    return servers.find(s => s.id === activeServerId) || null;
  }, [servers, activeServerId]);

  const activeTool = useMemo(() => {
    if (!activeServer) return null;
    return activeServer.tools.find(t => t.name === activeToolName) || null;
  }, [activeServer, activeToolName]);

  // Set active tool and clear arguments
  const selectTool = (tool: ToolSchema) => {
    setActiveToolName(tool.name);
    setPlaygroundArgs({});
    setPlaygroundOutput({ status: "idle" });
  };

  const handleArgChange = (name: string, val: any) => {
    setPlaygroundArgs(prev => ({
      ...prev,
      [name]: val
    }));
  };

  return (
    <div className="mcp-sandbox">
      <div className="mcp-sandbox__header">
        <div className="mcp-sandbox__header-title">
          <Shield size={18} className="text-purple" />
          <h2>MCP Tool Sandbox</h2>
        </div>
        <button 
          className="mcp-sandbox__refresh"
          onClick={() => fetchServers()}
          disabled={loading}
          title="Refresh Servers"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {/* Dynamic Import Bar */}
      <form className="mcp-import" onSubmit={handleImportServer}>
        <input 
          type="text" 
          placeholder="GitHub URL or git repository to import new MCP Server..."
          className="mcp-import__input"
          value={importUrl}
          onChange={(e) => setImportUrl(e.target.value)}
          disabled={importing}
        />
        <button 
          type="submit" 
          className="mcp-import__btn btn btn--purple" 
          disabled={importing || !importUrl.trim()}
        >
          {importing ? (
            <RefreshCw size={14} className="animate-spin" />
          ) : (
            <>
              <Plus size={14} />
              <span>Import</span>
            </>
          )}
        </button>
      </form>

      {loading ? (
        <div className="mcp-sandbox__loading">
          <RefreshCw size={24} className="animate-spin text-purple" />
          <p>Scanning active protocol registries...</p>
        </div>
      ) : (
        <div className="mcp-sandbox__content">
          {/* Sidebar: Servers list */}
          <div className="mcp-servers">
            <div className="mcp-servers__title">CONNECTED REGISTRIES</div>
            <div className="mcp-servers__list">
              {servers.map(server => (
                <button
                  key={server.id}
                  className={`mcp-server-item ${activeServerId === server.id ? "mcp-server-item--active" : ""}`}
                  onClick={() => {
                    setActiveServerId(server.id);
                    setActiveToolName(null);
                  }}
                >
                  <div className="mcp-server-item__header">
                    <Server size={14} className={server.type === "core" ? "text-cyan" : "text-purple"} />
                    <span className="mcp-server-item__name">{server.name}</span>
                  </div>
                  <div className="mcp-server-item__footer">
                    <span className={`mcp-server-item__badge mcp-server-item__badge--${server.type}`}>
                      {server.type.toUpperCase()}
                    </span>
                    <span className="mcp-server-item__tools-count">
                      {server.tools.length} tool{server.tools.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                </button>
              ))}
              {servers.length === 0 && (
                <div className="mcp-servers__empty">No MCP servers registered</div>
              )}
            </div>
          </div>

          {/* Details / Tools Panel */}
          <div className="mcp-details">
            {activeServer ? (
              <div className="mcp-active-server">
                <div className="mcp-active-server__meta">
                  <h3 className="mcp-active-server__name">{activeServer.name}</h3>
                  <div className="mcp-active-server__badges">
                    <span className={`mcp-badge mcp-badge--${activeServer.type}`}>
                      {activeServer.type} registry
                    </span>
                    <span className="mcp-badge mcp-badge--status">
                      <span className="mcp-badge__dot mcp-badge__dot--success"></span>
                      active
                    </span>
                  </div>
                </div>

                <div className="mcp-layout-split">
                  {/* Tools List */}
                  <div className="mcp-tools">
                    <div className="mcp-tools__title">AVAILABLE CAPABILITIES</div>
                    <div className="mcp-tools__list">
                      {activeServer.tools.map(tool => (
                        <div 
                          key={tool.name} 
                          className={`mcp-tool-card ${activeToolName === tool.name ? "mcp-tool-card--selected" : ""}`}
                          onClick={() => selectTool(tool)}
                        >
                          <div className="mcp-tool-card__header">
                            <span className="mcp-tool-card__name">{tool.name}</span>
                            <div className="mcp-permission-selector" onClick={e => e.stopPropagation()}>
                              <button 
                                className={`mcp-permission-btn mcp-permission-btn--allow ${tool.rule === "allow" ? "active" : ""}`}
                                onClick={() => handleUpdatePermission(tool.name, "allow")}
                                title="Allow automatically"
                              >
                                ALLOW
                              </button>
                              <button 
                                className={`mcp-permission-btn mcp-permission-btn--ask ${tool.rule === "ask" ? "active" : ""}`}
                                onClick={() => handleUpdatePermission(tool.name, "ask")}
                                title="Ask for manual steering approval"
                              >
                                ASK
                              </button>
                              <button 
                                className={`mcp-permission-btn mcp-permission-btn--deny ${tool.rule === "deny" ? "active" : ""}`}
                                onClick={() => handleUpdatePermission(tool.name, "deny")}
                                title="Completely disable"
                              >
                                DENY
                              </button>
                            </div>
                          </div>
                          <p className="mcp-tool-card__desc">{tool.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Playgrounds Panel */}
                  <div className="mcp-playground">
                    <div className="mcp-playground__title">SANDBOX PLAYGROUND</div>
                    
                    {activeTool ? (
                      <div className="mcp-playground__content">
                        <div className="mcp-playground__header">
                          <Terminal size={14} className="text-purple" />
                          <span className="mcp-playground__tool-name">{activeTool.name}</span>
                        </div>

                        {/* Parameter Form */}
                        <div className="mcp-playground__form">
                          {Object.entries(activeTool.inputSchema?.properties || {}).map(([paramName, paramInfo]) => {
                            const isRequired = activeTool.inputSchema?.required?.includes(paramName) || false;
                            
                            return (
                              <div key={paramName} className="mcp-param-group">
                                <label className="mcp-param-label">
                                  {paramName}
                                  {isRequired && <span className="mcp-param-required">*</span>}
                                  <span className="mcp-param-type">({paramInfo.type})</span>
                                </label>
                                
                                {paramInfo.description && (
                                  <span className="mcp-param-desc">{paramInfo.description}</span>
                                )}

                                {paramInfo.type === "boolean" ? (
                                  <div className="mcp-toggle-wrapper">
                                    <input 
                                      type="checkbox" 
                                      id={`param-${paramName}`}
                                      className="mcp-toggle-checkbox"
                                      checked={playgroundArgs[paramName] || false}
                                      onChange={(e) => handleArgChange(paramName, e.target.checked)}
                                    />
                                    <label htmlFor={`param-${paramName}`} className="mcp-toggle-slider"></label>
                                  </div>
                                ) : paramInfo.type === "object" || paramInfo.type === "array" ? (
                                  <textarea 
                                    className="mcp-textarea"
                                    placeholder={`Enter JSON object representing ${paramName}...`}
                                    value={playgroundArgs[paramName] !== undefined ? (typeof playgroundArgs[paramName] === "string" ? playgroundArgs[paramName] : JSON.stringify(playgroundArgs[paramName], null, 2)) : ""}
                                    onChange={(e) => {
                                      try {
                                        // Attempt soft validation
                                        if (e.target.value.trim() === "") {
                                          handleArgChange(paramName, undefined);
                                        } else {
                                          handleArgChange(paramName, e.target.value);
                                        }
                                      } catch { /* intentional */ }
                                    }}
                                  />
                                ) : paramInfo.type === "number" || paramInfo.type === "integer" ? (
                                  <input 
                                    type="number" 
                                    className="mcp-input" 
                                    value={playgroundArgs[paramName] || ""}
                                    onChange={(e) => handleArgChange(paramName, Number(e.target.value))}
                                  />
                                ) : (
                                  <input 
                                    type="text" 
                                    className="mcp-input" 
                                    value={playgroundArgs[paramName] || ""}
                                    onChange={(e) => handleArgChange(paramName, e.target.value)}
                                  />
                                )}
                              </div>
                            );
                          })}

                          {Object.keys(activeTool.inputSchema?.properties || {}).length === 0 && (
                            <div className="mcp-param-empty">
                              No parameters required for this tool.
                            </div>
                          )}

                          <button 
                            className="btn btn--purple mcp-playground__execute-btn"
                            disabled={playgroundOutput.status === "running" || activeTool.rule === "deny"}
                            onClick={() => {
                              // Deep parse any JSON inputs if they're stored as raw strings
                              const finalArgs: Record<string, any> = {};
                              for (const [k, v] of Object.entries(playgroundArgs)) {
                                if (v !== undefined) {
                                  const propSchema = activeTool.inputSchema.properties[k];
                                  if ((propSchema.type === "object" || propSchema.type === "array") && typeof v === "string") {
                                    try {
                                      finalArgs[k] = JSON.parse(v);
                                    } catch (_err) {
                                      // Fallback to raw value
                                      finalArgs[k] = v;
                                    }
                                  } else {
                                    finalArgs[k] = v;
                                  }
                                }
                              }
                              handleRunPlayground(activeTool.name);
                            }}
                          >
                            {playgroundOutput.status === "running" ? (
                              <>
                                <RefreshCw size={14} className="animate-spin" />
                                <span>Running tool...</span>
                              </>
                            ) : (
                              <>
                                <Play size={14} fill="currentColor" />
                                <span>Execute Tool</span>
                              </>
                            )}
                          </button>
                        </div>

                        {/* Output Console */}
                        <div className="mcp-playground__console">
                          <div className="mcp-playground__console-header">
                            <span>EXECUTION OUTPUT</span>
                            {playgroundOutput.status !== "idle" && (
                              <button 
                                className="mcp-playground__console-clear"
                                onClick={() => setPlaygroundOutput({ status: "idle" })}
                              >
                                Clear
                              </button>
                            )}
                          </div>
                          
                          <div className={`mcp-playground__console-body mcp-playground__console-body--${playgroundOutput.status}`}>
                            {playgroundOutput.status === "idle" && (
                              <div className="mcp-console-placeholder">
                                Waiting for tool execution...
                              </div>
                            )}

                            {playgroundOutput.status === "running" && (
                              <div className="mcp-console-running">
                                <RefreshCw size={16} className="animate-spin text-purple" />
                                <span>Invoking tool over secure container interface...</span>
                              </div>
                            )}

                            {playgroundOutput.status === "success" && (
                              <pre className="mcp-console-code">
                                {JSON.stringify(playgroundOutput.result, null, 2)}
                              </pre>
                            )}

                            {playgroundOutput.status === "error" && (
                              <div className="mcp-console-error">
                                <AlertTriangle size={16} />
                                <span>{playgroundOutput.error}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="mcp-playground__empty">
                        <Terminal size={32} className="text-muted" />
                        <p>Select a tool capability from the left to configure manual arguments and run in the sandbox</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="mcp-details__empty">
                <Server size={48} className="text-muted" />
                <p>Select a connected registry from the list to manage granular execution boundaries and playgrounds.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
