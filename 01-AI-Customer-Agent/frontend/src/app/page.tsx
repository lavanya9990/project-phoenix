"use client";

import { useEffect, useState } from "react";

type Message = {
  role: "user" | "bot";
  text: string;
};

type BusinessConfig = {
  welcome_message: string;
};

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onresult:
  | ((event: {
    results: {
      [index: number]: {
        [index: number]: {
          transcript: string;
        };
      };
    };
  }) => void)
  | null;
};

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  }
}

const quickQuestions = [
  "What are your business hours?",
  "Where are you located?",
  "Book appointment",
  "How can I contact support?",
];

const languages = [
  {
    label: "English",
    value: "en-IN",
  },
  {
    label: "Hindi",
    value: "hi-IN",
  },
  {
    label: "Telugu",
    value: "te-IN",
  },
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [selectedLanguage, setSelectedLanguage] = useState("en-IN");
  const [voiceError, setVoiceError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadWelcomeMessage() {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/business-config",
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error("Backend request failed");
        }

        const config: BusinessConfig = await response.json();
        setMessages((previousMessages) => [
          { role: "bot", text: config.welcome_message },
          ...previousMessages,
        ]);
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        setMessages((previousMessages) => [
          {
            role: "bot",
            text: "Sorry, I could not connect to the backend. Please check if FastAPI is running.",
          },
          ...previousMessages,
        ]);
      }
    }

    void loadWelcomeMessage();

    return () => controller.abort();
  }, []);

  function speakText(text: string) {
    if (!voiceEnabled) return;

    if (!("speechSynthesis" in window)) {
      setVoiceError("Text-to-speech is not supported in this browser.");
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = selectedLanguage;
    utterance.rate = 0.95;
    utterance.pitch = 1;

    window.speechSynthesis.speak(utterance);
  }

  function stopSpeaking() {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  }

  function startListening() {
    setVoiceError("");

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setVoiceError(
        "Speech recognition is not supported in this browser. Please try Chrome or Edge."
      );
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = selectedLanguage;
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      setVoiceError(`Voice error: ${event.error}`);
    };

    recognition.onresult = (event) => {
      const spokenText = event.results[0][0].transcript;
      setInput(spokenText);
      void sendMessage(spokenText, true);
    };

    recognition.start();
  }

  async function sendMessage(text: string, shouldSpeakReply = voiceEnabled) {
    if (!text.trim() || isLoading) return;

    const userMessage: Message = {
      role: "user",
      text,
    };

    setMessages((previousMessages) => [...previousMessages, userMessage]);
    setInput("");
    setIsLoading(true);
    setVoiceError("");

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

      if (shouldSpeakReply) {
        speakText(data.reply);
      }
    } catch {
      const errorText =
        "Sorry, I could not connect to the backend. Please check if FastAPI is running.";

      const errorMessage: Message = {
        role: "bot",
        text: errorText,
      };

      setMessages((previousMessages) => [...previousMessages, errorMessage]);

      if (shouldSpeakReply) {
        speakText(errorText);
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-100 flex items-center justify-center p-6">
      <div className="w-full max-w-3xl bg-white rounded-2xl shadow-lg flex flex-col overflow-hidden">
        <div className="bg-black text-white p-5 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">AI Voice Receptionist Demo</h1>
            <p className="text-sm text-gray-300">
              Speak or type to ask questions and book appointments
            </p>
          </div>

          <a
            href="/leads"
            className="bg-white text-black px-4 py-2 rounded-xl text-sm font-medium hover:bg-gray-200"
          >
            View Leads
          </a>
        </div>

        <div className="p-4 border-b space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <select
              value={selectedLanguage}
              onChange={(event) => setSelectedLanguage(event.target.value)}
              className="border rounded-xl px-4 py-2 text-gray-900"
            >
              {languages.map((language) => (
                <option key={language.value} value={language.value}>
                  {language.label}
                </option>
              ))}
            </select>

            <button
              onClick={startListening}
              disabled={isListening || isLoading}
              className={`px-5 py-2 rounded-xl font-medium text-white ${isListening ? "bg-red-600" : "bg-black hover:bg-gray-800"
                } disabled:opacity-50`}
            >
              {isListening ? "Listening..." : "Speak"}
            </button>

            <button
              onClick={() => setVoiceEnabled((previous) => !previous)}
              className="border border-gray-300 px-5 py-2 rounded-xl text-gray-800 hover:bg-gray-100"
            >
              Bot Voice: {voiceEnabled ? "ON" : "OFF"}
            </button>

            <button
              onClick={stopSpeaking}
              className="border border-gray-300 px-5 py-2 rounded-xl text-gray-800 hover:bg-gray-100"
            >
              Stop Voice
            </button>
          </div>

          {voiceError && (
            <p className="text-sm text-red-600 font-medium">{voiceError}</p>
          )}

          <div>
            <p className="text-sm font-medium text-gray-700 mb-3">
              Try asking:
            </p>

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
        </div>

        <div className="flex-1 p-5 space-y-4 h-[500px] overflow-y-auto">
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
            placeholder="Type your message or use Speak..."
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
