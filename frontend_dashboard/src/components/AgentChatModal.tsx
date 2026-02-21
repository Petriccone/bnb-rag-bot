"use client";

import React, { useState, useRef, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { X, Send, Bot, Loader2, RotateCcw } from 'lucide-react';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

interface AgentChatModalProps {
    agentId: string;
    agentName: string;
    agentNiche?: string;
    onClose: () => void;
}

export default function AgentChatModal({ agentId, agentName, agentNiche, onClose }: AgentChatModalProps) {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: 'assistant',
            content: `Olá! Sou ${agentName}${agentNiche ? `, especialista em ${agentNiche}` : ''}. Como posso ajudar você hoje?`,
            timestamp: new Date(),
        }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    const sendMessage = async () => {
        const text = input.trim();
        if (!text || loading) return;

        const userMsg: Message = { role: 'user', content: text, timestamp: new Date() };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await apiClient.post(`/agents/${agentId}/chat`, { message: text });
            const reply = res.data?.reply || '...';
            setMessages(prev => [...prev, { role: 'assistant', content: reply, timestamp: new Date() }]);
        } catch {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Erro ao contatar o agente. Verifique se o backend está rodando.',
                timestamp: new Date()
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const resetChat = () => {
        setMessages([{
            role: 'assistant',
            content: `Olá! Sou ${agentName}${agentNiche ? `, especialista em ${agentNiche}` : ''}. Como posso ajudar você hoje?`,
            timestamp: new Date(),
        }]);
        setInput('');
    };

    const formatTime = (d: Date) => d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

    return (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
            <div
                className="w-full sm:w-[480px] h-[90vh] sm:h-[640px] flex flex-col bg-white dark:bg-[#0f1117] border border-gray-200 dark:border-[#1f2937] rounded-t-2xl sm:rounded-2xl shadow-2xl overflow-hidden"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 dark:from-[#1d4ed8] dark:to-[#1e3a8a] flex-shrink-0">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center">
                            <Bot className="h-5 w-5 text-white" />
                        </div>
                        <div>
                            <p className="text-sm font-bold text-white">{agentName}</p>
                            {agentNiche && <p className="text-xs text-blue-200">{agentNiche}</p>}
                        </div>
                        <span className="ml-2 inline-flex items-center gap-1 bg-green-500/20 text-green-300 text-[10px] font-semibold px-2 py-0.5 rounded-full border border-green-400/30">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                            Online
                        </span>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={resetChat}
                            title="Reiniciar conversa"
                            className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-all"
                        >
                            <RotateCcw className="h-4 w-4" />
                        </button>
                        <button onClick={onClose} className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-all">
                            <X className="h-4 w-4" />
                        </button>
                    </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 bg-gray-50 dark:bg-[#0b0e14]">
                    {messages.map((msg, i) => (
                        <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            {msg.role === 'assistant' && (
                                <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mr-2 mt-1 shadow-md">
                                    <Bot className="h-4 w-4 text-white" />
                                </div>
                            )}
                            <div className={`max-w-[80%] ${msg.role === 'user' ? '' : ''}`}>
                                <div className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap shadow-sm ${msg.role === 'user'
                                        ? 'bg-blue-600 text-white rounded-br-sm'
                                        : 'bg-white dark:bg-[#1f2937] text-gray-800 dark:text-gray-100 border border-gray-100 dark:border-[#374151] rounded-bl-sm'
                                    }`}>
                                    {msg.content}
                                </div>
                                <p className={`text-[10px] text-gray-400 mt-1 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                                    {formatTime(msg.timestamp)}
                                </p>
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mr-2 mt-1">
                                <Bot className="h-4 w-4 text-white" />
                            </div>
                            <div className="bg-white dark:bg-[#1f2937] border border-gray-100 dark:border-[#374151] px-4 py-3 rounded-2xl rounded-bl-sm shadow-sm">
                                <div className="flex items-center gap-1.5">
                                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="flex-shrink-0 px-4 py-3 bg-white dark:bg-[#0f1117] border-t border-gray-200 dark:border-[#1f2937]">
                    <div className="flex items-center gap-2 bg-gray-100 dark:bg-[#1f2937] rounded-xl px-4 py-2.5 focus-within:ring-2 focus-within:ring-blue-500/50 transition-all">
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Digite sua mensagem..."
                            disabled={loading}
                            className="flex-1 bg-transparent text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 outline-none disabled:opacity-60"
                        />
                        <button
                            onClick={sendMessage}
                            disabled={!input.trim() || loading}
                            className="p-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-95 flex-shrink-0"
                        >
                            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                        </button>
                    </div>
                    <p className="text-[10px] text-gray-400 text-center mt-2">Enter para enviar • Chat de teste do agente</p>
                </div>
            </div>
        </div>
    );
}
