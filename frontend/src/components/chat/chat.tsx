"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";

// Define message types
type MessageRole = "user" | "assistant";

interface Message {
  role: MessageRole;
  content: string;
}

// Define product type for recommendations
interface Product {
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
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message to the chat
    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    
    // Clear previous recommendations when user sends a new message
    setRecommendations([]);

    try {
      // Add a placeholder for the assistant's message
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "" },
      ]);
      
      // Use simple non-streaming fetch request
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          messages: [...messages, userMessage],
          stream: false  // Set to false for non-streaming
        }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      
      // Update the assistant message
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: "assistant", content: data.response },
      ]);
      
      // Set recommendations if available
      if (data.recommendations && data.recommendations.length > 0) {
        setRecommendations(data.recommendations);
      }
      
    } catch (error) {
      console.error("Error calling API:", error);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        {
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col w-full max-w-3xl mx-auto h-[80vh]">
      <Card className="flex-1 p-4 overflow-y-auto mb-2 max-h-[70vh]">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            Start a conversation by typing a message below
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`flex items-start gap-2 max-w-[80%] ${message.role === "user" ? "flex-row-reverse" : ""}`}
                >
                  <Avatar>
                    <div
                      className={`flex items-center justify-center w-full h-full bg-primary text-primary-foreground text-sm font-medium`}
                    >
                      {message.role === "user" ? "U" : "A"}
                    </div>
                  </Avatar>
                  <div
                    className={`rounded-lg p-3 ${message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}
                  >
                    {message.content}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Display recommendations if available */}
            {recommendations.length > 0 && (
              <div className="mt-4 space-y-2">
                <h3 className="font-medium text-lg">Recommendations</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {recommendations.map((product: Product) => (
                    <Card key={product.id} className="p-2 hover:shadow-md transition-shadow">
                      <div className="font-medium">{product.name}</div>
                      <div className="text-sm text-muted-foreground">{product.category}</div>
                      <div className="mt-1">
                        <span className="font-medium">${product.price}</span>
                      </div>
                      <div className="mt-1 text-sm grid grid-cols-2 gap-x-2 gap-y-1">
                        <div><span className="font-medium">Fabric:</span> {product.fabric}</div>
                        <div><span className="font-medium">Fit:</span> {product.fit}</div>
                        <div><span className="font-medium">Color:</span> {product.color}</div>
                        {product.pattern && (
                          <div><span className="font-medium">Pattern:</span> {product.pattern}</div>
                        )}
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Card>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={isLoading}
          className="flex-1"
        />
        <Button type="submit" disabled={isLoading || !input.trim()}>
          {isLoading ? "Sending..." : "Send"}
        </Button>
      </form>
    </div>
  );
}
