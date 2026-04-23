import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  const upstreamParams = new URLSearchParams();
  ["ticker", "status"].forEach((key) => {
    const val = searchParams.get(key);
    if (val !== null) upstreamParams.set(key, val);
  });

  const baseUrl = process.env.STRATEGY_API_BASE_URL || "http://localhost:8006";
  const apiKey = process.env.STRATEGY_API_KEY;
  console.log(`baseUrl: ${baseUrl}, apiKey: ${apiKey ? "****" : "not set"}`);
  const url = `${baseUrl}/api/v1/strategies?${upstreamParams.toString()}`;

  try {
    const upstream = await fetch(url, {
      cache: "no-store",
      headers: apiKey ? { "X-API-Key": apiKey } : {},
    });
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch (e) {
    console.error("Error fetching strategies:", e);
    return NextResponse.json({ error: "Failed to reach strategy service" }, { status: 502 });
  }
}

export async function POST(request: NextRequest) {
  const baseUrl = process.env.STRATEGY_API_BASE_URL || "http://localhost:8006";
  const apiKey = process.env.STRATEGY_API_KEY;

  const url = `${baseUrl}/api/v1/strategies/research`;

  try {
    const body = await request.json();
    const upstream = await fetch(url, {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...(apiKey ? { "X-API-Key": apiKey } : {}),
      },
      body: JSON.stringify(body),
    });
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json({ error: "Failed to reach strategy service" }, { status: 502 });
  }
}
