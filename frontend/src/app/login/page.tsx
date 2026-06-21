"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { setToken } from "@/services/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@nexus.dev");
  const [password, setPassword] = useState("admin");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/nexus-proxy/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Login failed");
        return;
      }
      setToken(data.access_token);
      router.push("/");
    } catch {
      setError("Could not reach the server. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-md">
      <div className="w-full max-w-sm bg-surface-container-lowest rounded-2xl border border-outline-variant/20 shadow-lg overflow-hidden">
        {/* Header */}
        <div className="p-xl border-b border-outline-variant/10 flex flex-col items-center gap-sm">
          <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center">
            <span
              className="material-symbols-outlined text-white text-2xl"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              auto_awesome
            </span>
          </div>
          <h1 className="font-headline-md text-headline-md font-bold text-primary">Aether AI</h1>
          <p className="text-body-md text-outline text-center">Sign in to your workspace</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-xl space-y-lg">
          <div className="space-y-sm">
            <label className="font-label-md text-label-md text-outline uppercase tracking-wider">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-surface-container border border-outline-variant/20 rounded-xl px-md py-3 text-body-lg text-on-surface focus:ring-2 focus:ring-primary/30 transition-all outline-none"
              placeholder="admin@nexus.dev"
              autoComplete="email"
            />
          </div>

          <div className="space-y-sm">
            <label className="font-label-md text-label-md text-outline uppercase tracking-wider">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-surface-container border border-outline-variant/20 rounded-xl px-md py-3 text-body-lg text-on-surface focus:ring-2 focus:ring-primary/30 transition-all outline-none"
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </div>

          {error && (
            <p className="text-error text-body-md bg-error-container/30 px-md py-sm rounded-lg">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-on-primary py-3 rounded-xl font-semibold hover:bg-primary/90 transition-all shadow-md shadow-primary/20 active:scale-95 disabled:opacity-50 disabled:scale-100"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>

          <p className="text-center text-xs text-outline">
            Default credentials: <span className="font-label-md text-on-surface-variant">admin@nexus.dev / admin</span>
          </p>
        </form>
      </div>
    </div>
  );
}
