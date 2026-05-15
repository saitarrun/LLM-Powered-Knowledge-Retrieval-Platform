import { NextRequest, NextResponse } from "next/server";

async function proxyRequest(req: NextRequest, slug: string[]) {
  const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8001";
  const searchParams = req.nextUrl.searchParams.toString();
  const query = searchParams ? `?${searchParams}` : "";
  
  // The frontend calls /nexus-proxy/..., but the backend expects /api/v1/...
  // Strip trailing slash to prevent FastAPI's 307 redirect which kills POST bodies
  const path = slug.join("/").replace(/\/$/, "");
  const targetUrl = `${BACKEND_URL}/api/v1/${path}${query}`;
  
  try {
    // Forward all headers from the incoming request
    const forwardHeaders = new Headers();
    const headersToForward = ["content-type", "authorization", "accept", "accept-encoding"];

    headersToForward.forEach(header => {
      const value = req.headers.get(header);
      if (value) {
        forwardHeaders.set(header, value);
      }
    });

    // Ensure Content-Type is set
    if (!forwardHeaders.has("content-type")) {
      forwardHeaders.set("Content-Type", "application/json");
    }

    const config: RequestInit = {
      method: req.method,
      headers: forwardHeaders,
      redirect: "follow",
    };

    if (req.method !== "GET" && req.method !== "HEAD") {
      config.body = await req.clone().blob();
    }

    const res = await fetch(targetUrl, config);
    
    const responseHeaders = new Headers();
    responseHeaders.set("Content-Type", res.headers.get("content-type") || "application/json");
    responseHeaders.set("Access-Control-Allow-Origin", "*");
    responseHeaders.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
    responseHeaders.set("Access-Control-Allow-Headers", "Content-Type, Authorization");

    // For Server-Sent Events stream
    if (res.headers.get("content-type")?.includes("text/event-stream") && res.body) {
        responseHeaders.set("Cache-Control", "no-cache");
        responseHeaders.set("Connection", "keep-alive");
        return new NextResponse(res.body, {
            status: res.status,
            statusText: res.statusText,
            headers: responseHeaders
        });
    }

    const data = await res.blob();
    return new NextResponse(data, {
      status: res.status,
      statusText: res.statusText,
      headers: responseHeaders
    });

  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    console.error("API Route Proxy Error:", error);
    return NextResponse.json(
      { 
        detail: "Proxy connection to backend failed", 
        error: message,
        target: targetUrl 
      }, 
      { status: 502 }
    );
  }
}

export async function GET(req: NextRequest, { params }: { params: Promise<{ slug: string[] }> }) {
  const resolvedParams = await params;
  return proxyRequest(req, resolvedParams.slug);
}
export async function POST(req: NextRequest, { params }: { params: Promise<{ slug: string[] }> }) {
  const resolvedParams = await params;
  return proxyRequest(req, resolvedParams.slug);
}
export async function DELETE(req: NextRequest, { params }: { params: Promise<{ slug: string[] }> }) {
  const resolvedParams = await params;
  return proxyRequest(req, resolvedParams.slug);
}
export async function PUT(req: NextRequest, { params }: { params: Promise<{ slug: string[] }> }) {
  const resolvedParams = await params;
  return proxyRequest(req, resolvedParams.slug);
}
