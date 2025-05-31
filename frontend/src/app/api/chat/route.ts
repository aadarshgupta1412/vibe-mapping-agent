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
    const { messages } = body;
    
    // Try to connect to the backend first
    try {
      // Call the backend API
      const backendResponse = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ messages }),
      });
      
      if (backendResponse.ok) {
        // If backend is available, return its response
        const data = await backendResponse.json();
        console.log("Backend response:", data);
        return NextResponse.json(data);
      } else {
        console.error("Backend error:", await backendResponse.text());
      }
    } catch (backendError) {
      console.log("Backend not available, falling back to mock responses", backendError);
      // Continue with mock responses if backend is not available
    }
    
    // Get the last user message
    const lastUserMessage = messages.filter((msg: {role: string; content: string}) => msg.role === "user").pop();
    
    // Mock response based on user query
    let response = "I'll help you find the perfect clothing based on your vibe! Would you like to specify any preferences for size or budget?";
    let recommendations: Product[] = [];
    
    // Simple keyword detection for demo purposes
    if (lastUserMessage) {
      const query = lastUserMessage.content.toLowerCase();
      
      if (query.includes("dress") || query.includes("dresses")) {
        response = "I see you're interested in dresses! Do you have a specific occasion in mind, like casual, formal, or something in between?";
      } else if (query.includes("top") || query.includes("shirt") || query.includes("blouse")) {
        response = "Looking for tops? What kind of sleeve length would you prefer - sleeveless, short sleeves, or long sleeves?";
      } else if (query.includes("jeans") || query.includes("pants") || query.includes("trousers")) {
        response = "For bottoms, would you prefer a relaxed fit or something more fitted?";
      } else if (query.includes("size")) {
        response = "Great! I'll note your size preference. Any specific style or occasion you're shopping for?";
      } else if (query.includes("budget") || query.includes("price")) {
        response = "Thanks for sharing your budget. What type of clothing item are you looking for?";
      } else if (query.includes("casual") || query.includes("everyday")) {
        response = "For casual wear, I'd recommend checking out our relaxed fit items. Would you prefer tops, bottoms, or dresses?";
        
        // Add mock recommendations for casual wear
        recommendations = [
          {
            "id": "T001",
            "name": "Sun-Dapple Floral Top",
            "category": "top",
            "price": 72,
            "fabric": "Linen",
            "fit": "Relaxed",
            "color": "Pastel yellow",
            "pattern": "Floral"
          },
          {
            "id": "J002",
            "name": "Urban Edge Jeans",
            "category": "bottom",
            "price": 95,
            "fabric": "Denim",
            "fit": "Slim",
            "color": "Dark blue",
            "pattern": "Solid"
          }
        ];
      } else if (query.includes("formal") || query.includes("elegant")) {
        response = "For more formal occasions, we have several elegant options. Are you looking for something in a specific color?";
        
        // Add mock recommendations for formal wear
        recommendations = [
          {
            "id": "B005",
            "name": "Power Move Blazer",
            "category": "outerwear",
            "price": 150,
            "fabric": "Wool blend",
            "fit": "Tailored",
            "color": "Black",
            "pattern": "Solid"
          },
          {
            "id": "S003",
            "name": "Silky Evening Skirt",
            "category": "bottom",
            "price": 85,
            "fabric": "Silk",
            "fit": "A-line",
            "color": "Deep burgundy",
            "pattern": "Solid"
          }
        ];
      }
    }
    
    return NextResponse.json({ response, recommendations });
  } catch (error) {
    console.error("Error processing chat request:", error);
    return NextResponse.json(
      { error: "Failed to process request" },
      { status: 500 }
    );
  }
}
