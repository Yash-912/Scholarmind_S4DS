"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { synthesize } from "@/lib/api";

interface Message {
    role: "user" | "assistant";
    content: string;
    papers?: any[];
    metrics?: any;
    hallucination_check?: any;
}

export function useChat() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () =>
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    useEffect(scrollToBottom, [messages]);

    const send = useCallback(
        async (input: string, queryType?: string) => {
            if (!input.trim() || loading) return;

            const userMsg: Message = { role: "user", content: input };
            setMessages((prev) => [...prev, userMsg]);
            setLoading(true);
            setError(null);

            try {
                const result = await synthesize({
                    query: input,
                    query_type: queryType || undefined,
                });
                const assistantMsg: Message = {
                    role: "assistant",
                    content: result.answer || "No response generated.",
                    papers: result.papers,
                    metrics: result.metrics,
                    hallucination_check: result.hallucination_check,
                };
                setMessages((prev) => [...prev, assistantMsg]);
            } catch (err: any) {
                setError(err.message);
                setMessages((prev) => [
                    ...prev,
                    { role: "assistant", content: `❌ Error: ${err.message}` },
                ]);
            } finally {
                setLoading(false);
            }
        },
        [loading]
    );

    const clear = useCallback(() => {
        setMessages([]);
        setError(null);
    }, []);

    return { messages, loading, error, send, clear, messagesEndRef };
}
