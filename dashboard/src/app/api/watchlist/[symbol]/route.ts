import { NextResponse } from "next/server";

const baseUrl = () =>
  process.env.WATCHLIST_API_BASE_URL || "http://localhost:8002";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ symbol: string }> }
) {
  const { symbol } = await params;
  try {
    const upstream = await fetch(
      `${baseUrl()}/api/v1/watchlist/${encodeURIComponent(symbol)}`,
      { method: "DELETE", cache: "no-store" }
    );
    if (upstream.status === 204) {
      return new NextResponse(null, { status: 204 });
    }
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { error: "Failed to reach watchlist service" },
      { status: 502 }
    );
  }
}
