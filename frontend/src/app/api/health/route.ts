import { NextResponse } from "next/server";

export async function GET() {
  const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${BACKEND_URL}/api/health`, { cache: "no-store" });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ status: "unavailable" }, { status: 503 });
  }
}
