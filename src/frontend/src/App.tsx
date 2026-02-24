import React, { useState, useRef, useEffect } from "react";
import { getChatEndpoint, getAuthHeaders, getUserId } from "./config";

/** Shape of a tool call returned by the backend */
interface ToolCall {
  tool_name: string;
  arguments: Record<string, unknown>;
  result: string;
}

/** Shape of the backend chat response */
interface ChatApiResponse {
  conversation_id: number;
  response: string;
  tool_calls: ToolCall[];
}

/** A message in the chat thread */
interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls?: ToolCall[];
  timestamp: Date;
}

/** Suggested starter prompts */
const SUGGESTED_PROMPTS = [
  "Add a task to buy groceries",
  "Show me all my tasks",
  "What's pending?",
];

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [darkMode, setDarkMode] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async (messageText?: string) => {
    const text = (messageText || input).trim();
    if (!text || isLoading) return;

    setInput("");
    setError(null);

    // Add user message to thread
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
        throw new Error(
          errData.detail || `Server error (${res.status})`
        );
      }

      const data: ChatApiResponse = await res.json();

      // Track conversation ID for follow-up messages
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      // Add assistant message to thread
      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.response,
        toolCalls:
          data.tool_calls.length > 0 ? data.tool_calls : undefined,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Something went wrong";
      setError(message);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(null);
    setError(null);
    inputRef.current?.focus();
  };

  const bg = darkMode ? "#1a1a2e" : "#ffffff";
  const textColor = darkMode ? "#e0e0e0" : "#1a1a1a";
  const surfaceColor = darkMode ? "#16213e" : "#f5f5f5";
  const accentColor = "#6366f1";
  const userBubble = darkMode ? "#4338ca" : "#6366f1";
  const assistantBubble = darkMode ? "#1e293b" : "#f0f0f5";
  const borderColor = darkMode ? "#2d2d44" : "#e5e5e5";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        background: bg,
        color: textColor,
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}
    >
      {/* Header */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 20px",
          borderBottom: `1px solid ${borderColor}`,
          background: surfaceColor,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <h1
            style={{
              fontSize: "18px",
              fontWeight: 600,
              margin: 0,
            }}
          >
            Todo AI Assistant
          </h1>
          <span
            style={{
              fontSize: "12px",
              color: darkMode ? "#888" : "#999",
            }}
          >
            {getUserId()}
          </span>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            onClick={handleNewChat}
            style={{
              padding: "6px 14px",
              borderRadius: "8px",
              border: `1px solid ${borderColor}`,
              background: "transparent",
              color: textColor,
              cursor: "pointer",
              fontSize: "13px",
            }}
          >
            New Chat
          </button>
          <button
            onClick={() => setDarkMode(!darkMode)}
            style={{
              padding: "6px 14px",
              borderRadius: "8px",
              border: `1px solid ${borderColor}`,
              background: "transparent",
              color: textColor,
              cursor: "pointer",
              fontSize: "13px",
            }}
          >
            {darkMode ? "Light" : "Dark"}
          </button>
        </div>
      </header>

      {/* Messages area */}
      <main
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        {/* Start screen */}
        {messages.length === 0 && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              flex: 1,
              gap: "24px",
              textAlign: "center",
            }}
          >
            <div>
              <h2 style={{ fontSize: "24px", fontWeight: 600, margin: "0 0 8px" }}>
                Welcome to Todo AI Assistant
              </h2>
              <p style={{ color: darkMode ? "#888" : "#666", margin: 0 }}>
                Manage your tasks with natural language. Try one of these:
              </p>
            </div>
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "8px",
                justifyContent: "center",
              }}
            >
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => sendMessage(prompt)}
                  style={{
                    padding: "10px 18px",
                    borderRadius: "12px",
                    border: `1px solid ${borderColor}`,
                    background: surfaceColor,
                    color: textColor,
                    cursor: "pointer",
                    fontSize: "14px",
                    transition: "border-color 0.2s",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.borderColor = accentColor)
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.borderColor = borderColor)
                  }
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message bubbles */}
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: "flex",
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "100%",
            }}
          >
            <div
              style={{
                maxWidth: "min(80%, 600px)",
                padding: "12px 16px",
                borderRadius:
                  msg.role === "user"
                    ? "16px 16px 4px 16px"
                    : "16px 16px 16px 4px",
                background: msg.role === "user" ? userBubble : assistantBubble,
                color: msg.role === "user" ? "#fff" : textColor,
                fontSize: "15px",
                lineHeight: "1.5",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              {msg.content}

              {/* Tool call indicators */}
              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <div
                  style={{
                    marginTop: "10px",
                    paddingTop: "8px",
                    borderTop: `1px solid ${
                      darkMode ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.08)"
                    }`,
                    fontSize: "12px",
                    color: darkMode ? "#8b8fa3" : "#6b7280",
                  }}
                >
                  {msg.toolCalls.map((tc, i) => (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        marginTop: i > 0 ? "4px" : 0,
                      }}
                    >
                      <span
                        style={{
                          display: "inline-block",
                          width: "6px",
                          height: "6px",
                          borderRadius: "50%",
                          background: "#22c55e",
                        }}
                      />
                      <span>
                        Used <strong>{tc.tool_name}</strong>
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div style={{ display: "flex", justifyContent: "flex-start" }}>
            <div
              style={{
                padding: "12px 16px",
                borderRadius: "16px 16px 16px 4px",
                background: assistantBubble,
                fontSize: "15px",
                display: "flex",
                gap: "4px",
                alignItems: "center",
              }}
            >
              <span style={{ animation: "pulse 1.4s infinite", animationDelay: "0s" }}>.</span>
              <span style={{ animation: "pulse 1.4s infinite", animationDelay: "0.2s" }}>.</span>
              <span style={{ animation: "pulse 1.4s infinite", animationDelay: "0.4s" }}>.</span>
              <style>{`
                @keyframes pulse {
                  0%, 80%, 100% { opacity: 0.3; }
                  40% { opacity: 1; }
                }
              `}</style>
            </div>
          </div>
        )}

        {/* Error display */}
        {error && (
          <div
            style={{
              padding: "12px 16px",
              borderRadius: "12px",
              background: darkMode
                ? "rgba(239,68,68,0.15)"
                : "rgba(239,68,68,0.08)",
              color: "#ef4444",
              fontSize: "14px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              style={{
                background: "none",
                border: "none",
                color: "#ef4444",
                cursor: "pointer",
                fontSize: "16px",
                padding: "0 4px",
              }}
            >
              x
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Input area */}
      <footer
        style={{
          padding: "16px 20px",
          borderTop: `1px solid ${borderColor}`,
          background: surfaceColor,
        }}
      >
        <div
          style={{
            display: "flex",
            gap: "10px",
            maxWidth: "800px",
            margin: "0 auto",
          }}
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            disabled={isLoading}
            style={{
              flex: 1,
              padding: "12px 16px",
              borderRadius: "12px",
              border: `1px solid ${borderColor}`,
              background: bg,
              color: textColor,
              fontSize: "15px",
              outline: "none",
              transition: "border-color 0.2s",
            }}
            onFocus={(e) => (e.target.style.borderColor = accentColor)}
            onBlur={(e) => (e.target.style.borderColor = borderColor)}
          />
          <button
            onClick={() => sendMessage()}
            disabled={isLoading || !input.trim()}
            style={{
              padding: "12px 24px",
              borderRadius: "12px",
              border: "none",
              background:
                isLoading || !input.trim()
                  ? darkMode
                    ? "#2d2d44"
                    : "#e5e5e5"
                  : accentColor,
              color:
                isLoading || !input.trim()
                  ? darkMode
                    ? "#555"
                    : "#999"
                  : "#fff",
              cursor: isLoading || !input.trim() ? "default" : "pointer",
              fontSize: "15px",
              fontWeight: 500,
              transition: "background 0.2s",
            }}
          >
            Send
          </button>
        </div>
      </footer>
    </div>
  );
}
