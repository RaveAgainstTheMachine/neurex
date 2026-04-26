import { useState } from "react";
import { useStore } from "../../lib/store";
import { Lock, User, Shield, ArrowRight, Loader2, Cpu } from "lucide-react";
import "./AuthOverlay.css";
import toast from "react-hot-toast";

const API_BASE = "http://127.0.0.1:8000";

export function AuthOverlay() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const setAuth = useStore(s => s.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;

    setLoading(true);
    try {
      const endpoint = isLogin ? "/api/auth/token" : "/api/auth/register";
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Authentication failed");
      }

      if (!isLogin) {
        toast.success("Account created! Please sign in.");
        setIsLogin(true);
        setLoading(false);
        return;
      }

      const data = await res.json();
      const userRes = await fetch(`${API_BASE}/api/auth/me`, {
        headers: { "Authorization": `Bearer ${data.access_token}` }
      });
      const userData = await userRes.json();
      
      setAuth(data.access_token, userData);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-overlay">
      <div className="auth-mesh-bg" />
      <div className="auth-card glass">
        <div className="auth-card__header">
          <div className="auth-logo">
            <div className="auth-logo__inner">⬡</div>
          </div>
          <h2>{isLogin ? "Neural Link Established" : "Synthesize New Identity"}</h2>
          <p className="text-muted">
            {isLogin 
              ? "Accessing the Neurex Federated Mesh" 
              : "Register your presence in the global compute swarm"}
          </p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-input-group">
            <div className="auth-input">
              <User size={18} className="auth-input__icon" />
              <input 
                type="text" 
                placeholder="Username" 
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="auth-input">
              <Lock size={18} className="auth-input__icon" />
              <input 
                type="password" 
                placeholder="Password" 
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button className="btn btn--purple auth-submit" disabled={loading}>
            {loading ? <Loader2 className="animate-spin" /> : (
              <>
                {isLogin ? "Connect" : "Register"}
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <button className="auth-toggle" onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? "Request Mesh Access (Register)" : "Identify Presence (Login)"}
          </button>
        </div>

        <div className="auth-badge">
          <Shield size={12} />
          Encrypted Connection Active
        </div>
      </div>
    </div>
  );
}
