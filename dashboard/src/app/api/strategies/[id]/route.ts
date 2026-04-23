import { NextRequest, NextResponse } from "next/server";

const getBase = () =>
  process.env.STRATEGY_API_BASE_URL || "http://localhost:8006";
const getHeaders = (): Record<string, string> => {
  const apiKey = process.env.STRATEGY_API_KEY;
  return apiKey ? { "X-API-Key": apiKey } : {};
};

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const url = `${getBase()}/api/v1/strategies/${id}`;
  try {
    const upstream = await fetch(url, {
      cache: "no-store",
      headers: getHeaders(),
    });
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { error: "Failed to reach strategy service" },
      { status: 502 }
    );
  }
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const url = `${getBase()}/api/v1/strategies/${id}`;
  try {
    const upstream = await fetch(url, {
      method: "DELETE",
      cache: "no-store",
      headers: getHeaders(),
    });
    if (upstream.status === 204) {
      return new NextResponse(null, { status: 204 });
    }
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { error: "Failed to reach strategy service" },
      { status: 502 }
    );
  }
}
