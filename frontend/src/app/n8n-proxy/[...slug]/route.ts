import { NextRequest, NextResponse } from "next/server";

async function proxyRequest(req: NextRequest, slug: string[]) {
  const n8nUrl = process.env.N8N_URL || "http://n8n:5678";
  const targetUrl = `${n8nUrl}/webhook/${slug.join("/")}`;
  
  try {
    const config: RequestInit = {
      method: req.method,
      headers: {
        "Content-Type": req.headers.get("content-type") || "application/json",
      },
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

export async function GET(req: NextRequest, { params }: { params: Promise<{ slug: string[] }> }) {
  const resolvedParams = await params;
  return proxyRequest(req, resolvedParams.slug);
}
