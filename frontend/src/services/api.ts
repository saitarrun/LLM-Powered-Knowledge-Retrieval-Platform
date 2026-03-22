export const API_URL = "/nexus-proxy";

export const api = {
  API_URL,
  // Documents
  async getDocuments() {
    try {
      const res = await fetch(`${API_URL}/documents/`);
      if (!res.ok) return [];
      return res.json();
    } catch {
      return [];
    }
  },

  async getGraph() {
    try {
      const res = await fetch(`${API_URL}/documents/graph`);
      if (!res.ok) return { nodes: [], links: [] };
      return res.json();
    } catch {
      return { nodes: [], links: [] };
    }
  },
  
  async getStatus() {
    try {
      const res = await fetch(`${API_URL}/documents/status/`);
      if (!res.ok) return { documents: 0, indexed_chunks: 0, average_latency: 0 };
      return res.json();
    } catch {
      return { documents: 0, indexed_chunks: 0, average_latency: 0 };
    }
  },

  async getAnalytics() {
    try {
      const res = await fetch(`${API_URL}/documents/analytics`);
      if (!res.ok) return null;
      return res.json();
    } catch {
      return null;
    }
  },

  async uploadDocument(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_URL}/documents/upload/`, {
      method: "POST",
      body: formData,
    });
    return res.json();
  },

  async uploadToN8N(file: File) {
    const formData = new FormData();
    formData.append("data", file);
    const res = await fetch(`/n8n-proxy/ingest`, {
      method: "POST",
      body: formData,
    });
    return res.json();
  },

  async resumeN8N(resumeUrl: string) {
    const res = await fetch(resumeUrl, { method: "GET" });
    return res.json();
  },

  async deleteDocument(id: string) {
    const res = await fetch(`${API_URL}/documents/${id}/`, {
      method: "DELETE",
    });
    return res.json();
  },

  // Chat
  async queryChat(query: string, top_k: number = 5) {
    const res = await fetch(`${API_URL}/chat/query/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k, use_hybrid_search: false, use_reranker: true }),
    });
    return res.json();
  },

  async sendFeedback(query_id: string, feedback: number) {
    const res = await fetch(`${API_URL}/chat/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query_id, feedback }),
    });
    return res.json();
  },

  // Settings
  async getSettings() {
    const res = await fetch(`${API_URL}/settings/`);
    return res.json();
  },

  async updateSettings(settings: Record<string, unknown>) {
    const res = await fetch(`${API_URL}/settings/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });
    return res.json();
  }
};
