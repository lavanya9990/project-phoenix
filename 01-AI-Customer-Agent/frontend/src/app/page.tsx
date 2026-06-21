"use client";

import { useState } from "react";

type Message = {
  role: "user" | "bot";
  text: string;
};

const quickQuestions = [
  "What are your business hours?",
  "Where are you located?",
  "Do you offer appointments?",
  "How can I contact support?",
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "bot",
      text: "Hi! I am your AI customer support assistant. How can I help you today?",
    },
  ]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function sendMessage(text: string) {
    if (!text.trim() || isLoading) return;

    const userMessage: Message = {
      role: "user",
      text,
    };

    setMessages((previousMessages) => [...previousMessages, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
        }),
      });

      if (!response.ok) {
        throw new Error("Backend request failed");
      }

      const data: { reply: string } = await response.json();

      const botMessage: Message = {
        role: "bot",
        text: data.reply,
      };

      setMessages((previousMessages) => [...previousMessages, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        role: "bot",
        text: "Sorry, I could not connect to the backend. Please check if FastAPI is running.",
      };

      setMessages((previousMessages) => [...previousMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-100 flex items-center justify-center p-6">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-lg flex flex-col overflow-hidden">
        <div className="bg-black text-white p-5">
          <h1 className="text-2xl font-bold">AI Customer Support Agent</h1>
          <p className="text-sm text-gray-300">
            Full-stack demo using Next.js frontend and FastAPI backend
          </p>
        </div>

        <div className="p-4 border-b">
          <p className="text-sm font-medium text-gray-700 mb-3">Try asking:</p>

          <div className="flex flex-wrap gap-2">
            {quickQuestions.map((question) => (
              <button
                key={question}
                onClick={() => sendMessage(question)}
                disabled={isLoading}
                className="text-sm border border-gray-300 rounded-full px-4 py-2 hover:bg-gray-100 text-gray-800 disabled:opacity-50"
              >
                {question}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 p-5 space-y-4 h-[420px] overflow-y-auto">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"
                }`}
            >
              <div
                className={`max-w-[75%] rounded-xl px-4 py-3 text-sm leading-relaxed ${message.role === "user"
                  ? "bg-black text-white"
                  : "bg-gray-200 text-gray-900"
                  }`}
              >
                {message.text}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-200 text-gray-900 rounded-xl px-4 py-3 text-sm">
                Thinking...
              </div>
            </div>
          )}
        </div>

        <div className="border-t p-4 flex gap-3">
          <input
            className="flex-1 border rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-black text-black placeholder:text-gray-400"
            placeholder="Type your message..."
            value={input}
            disabled={isLoading}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                sendMessage(input);
              }
            }}
          />

          <button
            onClick={() => sendMessage(input)}
            disabled={isLoading}
            className="bg-black text-white px-6 py-3 rounded-xl font-medium hover:bg-gray-800 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </main>
  );
}