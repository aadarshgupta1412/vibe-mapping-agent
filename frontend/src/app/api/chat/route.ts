import { NextRequest, NextResponse } from "next/server";

// Define product type
type Product = {
  id: string;
  name: string;
  category: string;
  price: number;
  fabric: string;
  fit: string;
  color: string;
  pattern?: string;
  style?: string[];
  occasion?: string[];
};

// Backend URL
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { messages, stream = false } = body;
    
    // Call the backend API
    const backendResponse = await fetch(`${BACKEND_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ messages, stream }),
    });
    
    if (!backendResponse.ok) {
      console.error("Backend error:", await backendResponse.text());
      return NextResponse.json(
        { error: `Backend error: ${backendResponse.status}` },
        { status: backendResponse.status }
      );
    }
    
    // If streaming is requested, pass through the stream directly
    if (stream) {
      // Create a streaming response
      const streamingResponse = new Response(backendResponse.body);
      
      // Copy headers from backend response
      backendResponse.headers.forEach((value, key) => {
        streamingResponse.headers.set(key, value);
      });
      
      // Ensure proper headers for SSE
      streamingResponse.headers.set("Content-Type", "text/event-stream");
      streamingResponse.headers.set("Cache-Control", "no-cache");
      streamingResponse.headers.set("Connection", "keep-alive");
      
      return streamingResponse;
    } else {
      // For regular responses, return the JSON
      const data = await backendResponse.json();
      console.log("Backend response:", data);
      return NextResponse.json(data);
    }
  } catch (error) {
    console.error("Error in chat API:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
