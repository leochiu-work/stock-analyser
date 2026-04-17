import { NextRequest, NextResponse } from "next/server";

const baseUrl = () =>
  process.env.WATCHLIST_API_BASE_URL || "http://localhost:8002";

export async function GET() {
  try {
    const upstream = await fetch(`${baseUrl()}/api/v1/watchlist`, {
      cache: "no-store",
    });
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { error: "Failed to reach watchlist service" },
      { status: 502 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const upstream = await fetch(`${baseUrl()}/api/v1/watchlist`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { error: "Failed to reach watchlist service" },
      { status: 502 }
    );
  }
}
