import React, { useState, useRef, useEffect } from "react";
import { getChatEndpoint, getAuthHeaders, getUserId } from "./config";

interface ToolCall {
  tool_name: string;
  arguments: Record<string, unknown>;
  result: string;
}

interface ChatApiResponse {
  conversation_id: number;
  response: string;
  tool_calls: ToolCall[];
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls?: ToolCall[];
  timestamp: Date;
}

const SUGGESTED_PROMPTS = [
  { icon: "✅", text: "Add a task to buy groceries" },
  { icon: "📋", text: "Show me all my tasks" },
  { icon: "⏳", text: "What's pending?" },
  { icon: "🎯", text: "Mark task 1 as complete" },
];

const GLOBAL_STYLES = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
  }

  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.3); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.6); }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes dotBounce {
    0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
    40%           { transform: translateY(-6px); opacity: 1; }
  }
  @keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position:  200% center; }
  }
  @keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
  @keyframes pulse-ring {
    0%   { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(99,102,241,0.5); }
    70%  { transform: scale(1);    box-shadow: 0 0 0 8px rgba(99,102,241,0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(99,102,241,0); }
  }

  .msg-appear { animation: fadeUp 0.3s ease forwards; }

  .send-btn {
    position: relative;
    overflow: hidden;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .send-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 8px 25px rgba(99,102,241,0.45);
  }
  .send-btn:active:not(:disabled) { transform: translateY(0); }

  .prompt-chip {
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  }
  .prompt-chip:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99,102,241,0.25);
    border-color: rgba(99,102,241,0.7) !important;
  }

  .header-btn {
    transition: background 0.15s ease, transform 0.15s ease;
  }
  .header-btn:hover { transform: translateY(-1px); }
`;

export default function App() {
  const [messages, setMessages]           = useState<ChatMessage[]>([]);
  const [input, setInput]                 = useState("");
  const [isLoading, setIsLoading]         = useState(false);
  const [error, setError]                 = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [darkMode, setDarkMode]           = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef       = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const sendMessage = async (messageText?: string) => {
    const text = (messageText || input).trim();
    if (!text || isLoading) return;
    setInput("");
    setError(null);

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const res = await fetch(getChatEndpoint(), {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          message: text,
          ...(conversationId ? { conversation_id: conversationId } : {}),
        }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error (${res.status})`);
      }
      const data: ChatApiResponse = await res.json();
      if (data.conversation_id) setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.response,
          toolCalls: data.tool_calls.length > 0 ? data.tool_calls : undefined,
          timestamp: new Date(),
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(null);
    setError(null);
    inputRef.current?.focus();
  };

  /* ── Design tokens ── */
  const dark = darkMode;
  const surface   = dark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.85)";
  const border    = dark ? "rgba(255,255,255,0.08)" : "rgba(99,102,241,0.15)";
  const text      = dark ? "#e8eaf6" : "#1a1a2e";
  const muted     = dark ? "#7b7fa8" : "#8890b5";
  const accent    = "#6366f1";
  const accent2   = "#8b5cf6";

  const glassBg   = dark
    ? "rgba(255,255,255,0.05)"
    : "rgba(255,255,255,0.7)";

  return (
    <>
      <style>{GLOBAL_STYLES}</style>

      <div style={{
        display: "flex", flexDirection: "column", height: "100vh",
        background: dark
          ? "linear-gradient(135deg, #0d0d1a 0%, #111128 50%, #0d1033 100%)"
          : "linear-gradient(135deg, #eef0ff 0%, #f5f0ff 50%, #eaf4ff 100%)",
        color: text,
        fontFamily: "'Inter', sans-serif",
        position: "relative",
        overflow: "hidden",
      }}>

        {/* Background orbs */}
        <div style={{
          position: "absolute", inset: 0, pointerEvents: "none", zIndex: 0,
          overflow: "hidden",
        }}>
          <div style={{
            position: "absolute", top: "-20%", left: "-10%",
            width: "500px", height: "500px", borderRadius: "50%",
            background: dark
              ? "radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)"
              : "radial-gradient(circle, rgba(99,102,241,0.1) 0%, transparent 70%)",
          }} />
          <div style={{
            position: "absolute", bottom: "-10%", right: "-5%",
            width: "400px", height: "400px", borderRadius: "50%",
            background: dark
              ? "radial-gradient(circle, rgba(139,92,246,0.1) 0%, transparent 70%)"
              : "radial-gradient(circle, rgba(139,92,246,0.08) 0%, transparent 70%)",
          }} />
        </div>

        {/* ── Header ── */}
        <header style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "14px 24px",
          background: glassBg,
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          borderBottom: `1px solid ${border}`,
          position: "relative", zIndex: 10,
        }}>
          {/* Logo + title */}
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{
              width: "36px", height: "36px", borderRadius: "10px",
              background: `linear-gradient(135deg, ${accent}, ${accent2})`,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "18px", boxShadow: `0 4px 15px rgba(99,102,241,0.4)`,
              animation: "pulse-ring 2.5s infinite",
            }}>🤖</div>
            <div>
              <h1 style={{
                fontFamily: "'Poppins', sans-serif",
                fontSize: "17px", fontWeight: 700, margin: 0,
                background: `linear-gradient(90deg, ${accent}, ${accent2}, #ec4899)`,
                backgroundSize: "200% auto",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                animation: "shimmer 3s linear infinite",
              }}>
                Todo AI Assistant
              </h1>
              <div style={{
                fontSize: "11px", color: muted, marginTop: "1px",
                letterSpacing: "0.4px",
              }}>
                @{getUserId()}
              </div>
            </div>
          </div>

          {/* Header actions */}
          <div style={{ display: "flex", gap: "8px" }}>
            {[
              { label: "＋ New Chat", action: handleNewChat },
              { label: dark ? "☀ Light" : "🌙 Dark", action: () => setDarkMode(!dark) },
            ].map(({ label, action }) => (
              <button key={label} className="header-btn" onClick={action} style={{
                padding: "7px 14px",
                borderRadius: "10px",
                border: `1px solid ${border}`,
                background: surface,
                color: text,
                cursor: "pointer",
                fontSize: "12px",
                fontWeight: 500,
                fontFamily: "'Inter', sans-serif",
                letterSpacing: "0.3px",
              }}>{label}</button>
            ))}
          </div>
        </header>

        {/* ── Messages ── */}
        <main style={{
          flex: 1, overflowY: "auto", padding: "24px 20px",
          display: "flex", flexDirection: "column", gap: "16px",
          position: "relative", zIndex: 1,
        }}>
          {/* Welcome screen */}
          {messages.length === 0 && (
            <div style={{
              display: "flex", flexDirection: "column", alignItems: "center",
              justifyContent: "center", flex: 1, gap: "32px", textAlign: "center",
              animation: "fadeUp 0.5s ease",
            }}>
              {/* Big icon */}
              <div style={{
                width: "80px", height: "80px", borderRadius: "24px",
                background: `linear-gradient(135deg, ${accent}, ${accent2})`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "38px",
                boxShadow: `0 12px 40px rgba(99,102,241,0.4)`,
              }}>🤖</div>

              <div>
                <h2 style={{
                  fontFamily: "'Poppins', sans-serif",
                  fontSize: "28px", fontWeight: 800, margin: "0 0 10px",
                  background: `linear-gradient(135deg, ${text}, ${accent})`,
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}>
                  How can I help you today?
                </h2>
                <p style={{
                  color: muted, fontSize: "15px", margin: 0,
                  fontWeight: 400, letterSpacing: "0.2px",
                }}>
                  Manage your tasks with natural language. Try one of these:
                </p>
              </div>

              {/* Suggestion chips */}
              <div style={{
                display: "flex", flexWrap: "wrap", gap: "12px",
                justifyContent: "center", maxWidth: "600px",
              }}>
                {SUGGESTED_PROMPTS.map(({ icon, text: pText }) => (
                  <button
                    key={pText}
                    className="prompt-chip"
                    onClick={() => sendMessage(pText)}
                    style={{
                      padding: "12px 20px",
                      borderRadius: "14px",
                      border: `1px solid ${border}`,
                      background: glassBg,
                      backdropFilter: "blur(12px)",
                      color: text,
                      cursor: "pointer",
                      fontSize: "14px",
                      fontFamily: "'Inter', sans-serif",
                      fontWeight: 500,
                      display: "flex", alignItems: "center", gap: "8px",
                    }}
                  >
                    <span style={{ fontSize: "16px" }}>{icon}</span>
                    {pText}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Message bubbles */}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className="msg-appear"
              style={{
                display: "flex",
                justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
              }}
            >
              {/* Avatar for assistant */}
              {msg.role === "assistant" && (
                <div style={{
                  width: "32px", height: "32px", borderRadius: "10px",
                  background: `linear-gradient(135deg, ${accent}, ${accent2})`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "15px", flexShrink: 0, marginRight: "10px",
                  alignSelf: "flex-end",
                  boxShadow: `0 4px 12px rgba(99,102,241,0.35)`,
                }}>🤖</div>
              )}

              <div style={{
                maxWidth: "min(72%, 600px)",
                padding: "13px 18px",
                borderRadius: msg.role === "user"
                  ? "18px 18px 4px 18px"
                  : "18px 18px 18px 4px",
                background: msg.role === "user"
                  ? `linear-gradient(135deg, ${accent}, ${accent2})`
                  : glassBg,
                backdropFilter: msg.role === "assistant" ? "blur(12px)" : undefined,
                WebkitBackdropFilter: msg.role === "assistant" ? "blur(12px)" : undefined,
                border: msg.role === "assistant" ? `1px solid ${border}` : "none",
                color: msg.role === "user" ? "#fff" : text,
                fontSize: "14.5px",
                lineHeight: "1.65",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontWeight: 400,
                boxShadow: msg.role === "user"
                  ? "0 4px 20px rgba(99,102,241,0.35)"
                  : dark
                    ? "0 2px 12px rgba(0,0,0,0.3)"
                    : "0 2px 12px rgba(0,0,0,0.08)",
              }}>
                {msg.content}

                {/* Tool call badges */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div style={{
                    marginTop: "10px", paddingTop: "10px",
                    borderTop: `1px solid ${dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)"}`,
                    display: "flex", flexWrap: "wrap", gap: "6px",
                  }}>
                    {msg.toolCalls.map((tc, i) => (
                      <span key={i} style={{
                        display: "inline-flex", alignItems: "center", gap: "5px",
                        padding: "3px 10px", borderRadius: "20px",
                        background: dark
                          ? "rgba(34,197,94,0.15)"
                          : "rgba(34,197,94,0.1)",
                        border: "1px solid rgba(34,197,94,0.3)",
                        color: "#22c55e",
                        fontSize: "11.5px", fontWeight: 600,
                        letterSpacing: "0.3px",
                      }}>
                        ⚡ {tc.tool_name}
                      </span>
                    ))}
                  </div>
                )}

                {/* Timestamp */}
                <div style={{
                  marginTop: "6px",
                  fontSize: "10.5px",
                  color: msg.role === "user"
                    ? "rgba(255,255,255,0.55)"
                    : muted,
                  textAlign: msg.role === "user" ? "right" : "left",
                }}>
                  {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </div>
              </div>

              {/* Avatar for user */}
              {msg.role === "user" && (
                <div style={{
                  width: "32px", height: "32px", borderRadius: "10px",
                  background: dark ? "#2a2a3e" : "#e0e4ff",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "15px", flexShrink: 0, marginLeft: "10px",
                  alignSelf: "flex-end",
                  border: `1px solid ${border}`,
                }}>👤</div>
              )}
            </div>
          ))}

          {/* Typing indicator */}
          {isLoading && (
            <div className="msg-appear" style={{ display: "flex", alignItems: "flex-end", gap: "10px" }}>
              <div style={{
                width: "32px", height: "32px", borderRadius: "10px",
                background: `linear-gradient(135deg, ${accent}, ${accent2})`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "15px", boxShadow: `0 4px 12px rgba(99,102,241,0.35)`,
              }}>🤖</div>
              <div style={{
                padding: "14px 18px", borderRadius: "18px 18px 18px 4px",
                background: glassBg,
                backdropFilter: "blur(12px)",
                border: `1px solid ${border}`,
                display: "flex", gap: "5px", alignItems: "center",
              }}>
                {[0, 0.15, 0.3].map((delay, i) => (
                  <span key={i} style={{
                    width: "7px", height: "7px", borderRadius: "50%",
                    background: accent,
                    display: "inline-block",
                    animation: `dotBounce 1.2s ease-in-out infinite`,
                    animationDelay: `${delay}s`,
                  }} />
                ))}
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div style={{
              padding: "12px 18px", borderRadius: "14px",
              background: dark ? "rgba(239,68,68,0.12)" : "rgba(239,68,68,0.07)",
              border: "1px solid rgba(239,68,68,0.25)",
              color: "#f87171",
              fontSize: "13.5px", fontWeight: 500,
              display: "flex", justifyContent: "space-between", alignItems: "center",
              animation: "fadeUp 0.3s ease",
            }}>
              <span>⚠ {error}</span>
              <button onClick={() => setError(null)} style={{
                background: "none", border: "none", color: "#f87171",
                cursor: "pointer", fontSize: "18px", lineHeight: 1, padding: "0 4px",
              }}>×</button>
            </div>
          )}

          <div ref={messagesEndRef} />
        </main>

        {/* ── Input area ── */}
        <footer style={{
          padding: "16px 20px 20px",
          background: glassBg,
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          borderTop: `1px solid ${border}`,
          position: "relative", zIndex: 10,
        }}>
          <div style={{
            display: "flex", gap: "10px",
            maxWidth: "780px", margin: "0 auto",
            alignItems: "center",
          }}>
            <div style={{
              flex: 1, position: "relative",
              borderRadius: "14px",
              background: dark ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.9)",
              border: `1.5px solid ${border}`,
              transition: "border-color 0.2s, box-shadow 0.2s",
            }}
              onFocus={() => {}}
            >
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me to manage your tasks…"
                disabled={isLoading}
                style={{
                  width: "100%",
                  padding: "14px 18px",
                  background: "transparent",
                  border: "none", outline: "none",
                  color: text,
                  fontSize: "14.5px",
                  fontFamily: "'Inter', sans-serif",
                  fontWeight: 400,
                }}
                onFocus={(e) => {
                  const parent = e.target.parentElement!;
                  parent.style.borderColor = accent;
                  parent.style.boxShadow = `0 0 0 3px rgba(99,102,241,0.15)`;
                }}
                onBlur={(e) => {
                  const parent = e.target.parentElement!;
                  parent.style.borderColor = border;
                  parent.style.boxShadow = "none";
                }}
              />
            </div>

            <button
              className="send-btn"
              onClick={() => sendMessage()}
              disabled={isLoading || !input.trim()}
              style={{
                padding: "14px 22px",
                borderRadius: "14px",
                border: "none",
                background: isLoading || !input.trim()
                  ? dark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.06)"
                  : `linear-gradient(135deg, ${accent}, ${accent2})`,
                color: isLoading || !input.trim() ? muted : "#fff",
                cursor: isLoading || !input.trim() ? "default" : "pointer",
                fontSize: "14.5px",
                fontWeight: 600,
                fontFamily: "'Inter', sans-serif",
                letterSpacing: "0.3px",
                boxShadow: isLoading || !input.trim()
                  ? "none"
                  : "0 4px 15px rgba(99,102,241,0.35)",
                whiteSpace: "nowrap",
              }}
            >
              {isLoading ? "…" : "Send ↑"}
            </button>
          </div>

          <p style={{
            textAlign: "center", marginTop: "10px",
            fontSize: "11px", color: muted, letterSpacing: "0.3px",
          }}>
            Press <kbd style={{
              padding: "1px 6px", borderRadius: "4px",
              border: `1px solid ${border}`,
              background: dark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.05)",
              fontFamily: "monospace", fontSize: "11px",
            }}>Enter</kbd> to send &nbsp;·&nbsp; Todo AI Assistant v2.0
          </p>
        </footer>
      </div>
    </>
  );
}
