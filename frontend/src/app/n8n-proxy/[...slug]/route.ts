import { NextRequest, NextResponse } from "next/server";

async function proxyRequest(req: NextRequest, slug: string[]) {
  const n8nUrl = process.env.N8N_URL || "http://n8n:5678";
  
  // Forward to n8n webhook (or other n8n endpoints)
  // For webhooks, the URL is usually /webhook/..., but our proxy is /n8n-proxy/...
  const targetUrl = `${n8nUrl}/webhook/${slug.join("/")}`;
  
  try {
    const config: RequestInit = {
      method: req.method,
      headers: {
        // Carry over content-type for multipart/form-data support
        "Content-Type": req.headers.get("content-type") || "application/json",
      },
      // Increase timeout for large file uploads
      cache: "no-store",
    };
    
    if (req.method !== "GET" && req.method !== "HEAD") {
      config.body = await req.clone().blob();
    }

    const res = await fetch(targetUrl, config);
    
    const responseHeaders = new Headers();
    responseHeaders.set("Content-Type", res.headers.get("content-type") || "application/json");
    responseHeaders.set("Access-Control-Allow-Origin", "*");

    const data = await res.blob();
    return new NextResponse(data, {
      status: res.status,
      statusText: res.statusText,
      headers: responseHeaders
    });

  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    console.error("N8N Proxy Error:", error);
    return NextResponse.json(
      { 
        detail: "Proxy connection to n8n failed", 
        error: message,
        target: targetUrl 
      }, 
      { status: 502 }
    );
  }
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ slug: string[] }> }) {
  const resolvedParams = await params;
  return proxyRequest(req, resolvedParams.slug);
}

// Support GET for testing if needed
export async function GET(req: NextRequest, { params }: { params: Promise<{ slug: string[] }> }) {
  const resolvedParams = await params;
  return proxyRequest(req, resolvedParams.slug);
}
