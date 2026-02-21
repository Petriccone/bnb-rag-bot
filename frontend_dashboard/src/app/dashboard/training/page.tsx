"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useI18n } from '@/lib/i18n-context';
import { BookOpen, Upload, Database, CheckCircle, Play, FileText, Trash2, Loader2, Edit2, Check, X, Globe } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Document {
    id: string;
    file_name?: string;
    file_path: string;
    created_at: string;
    status?: string;
    embedding_namespace?: string;
}

export default function TrainingPage() {
    const { t } = useI18n();
    const [documents, setDocuments] = useState<Document[]>([]);
    const [agents, setAgents] = useState<any[]>([]);
    const [selectedAgent, setSelectedAgent] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [editingDocId, setEditingDocId] = useState<string | null>(null);
    const [editNameValue, setEditNameValue] = useState<string>('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    const fetchDocumentsAndAgents = async () => {
        try {
            setLoading(true);
            const [docRes, agentRes] = await Promise.all([
                apiClient.get('/documents'),
                apiClient.get('/agents')
            ]);
            setDocuments(docRes.data);
            setAgents(agentRes.data);
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchDocumentsAndAgents(); }, []);

    const handleUploadClick = () => fileInputRef.current?.click();

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;
        try {
            setUploading(true);
            let namespace = '';
            if (selectedAgent) {
                const agent = agents.find(a => a.id === selectedAgent);
                if (agent) {
                    namespace = agent.embedding_namespace;
                    if (!namespace) {
                        namespace = `agent_${agent.id}`;
                        await apiClient.patch(`/agents/${agent.id}`, { embedding_namespace: namespace });
                        setAgents(prev => prev.map(a => a.id === agent.id ? { ...a, embedding_namespace: namespace } : a));
                    }
                }
            }
            const formData = new FormData();
            formData.append('file', file);
            const uploadUrl = namespace
                ? `/documents/upload?embedding_namespace=${encodeURIComponent(namespace)}`
                : '/documents/upload';
            const response = await apiClient.post(uploadUrl, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
            if (response.status === 200 || response.status === 201) {
                await fetchDocumentsAndAgents();
            } else {
                alert('Erro ao enviar o documento.');
            }
        } catch {
            alert('Erro ao enviar o documento.');
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Tem certeza que deseja remover este documento?')) return;
        try {
            await apiClient.delete(`/documents/${id}`);
            setDocuments(prev => prev.filter(doc => doc.id !== id));
        } catch { /* error */ }
    };

    const formatDate = (dateString: string) => {
        if (!dateString) return '—';
        try {
            const d = new Date(dateString);
            if (isNaN(d.getTime())) return '—';
            return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
        } catch { return '—'; }
    };

    // Prefer file_name field; fallback to deriving from file_path (supports both / and \ separators)
    const getDisplayName = (doc: Document) => {
        if (doc.file_name && doc.file_name.trim()) return doc.file_name;
        const raw = doc.file_path || '';
        const parts = raw.replace(/\\/g, '/').split('/');
        const name = parts[parts.length - 1] || 'Documento';
        // If name looks like a UUID (no extension or only hex chars), return generic label
        if (/^[0-9a-f-]{32,}$/i.test(name.replace(/\.[^.]+$/, ''))) return 'Documento sem nome';
        return name;
    };

    const getFileType = (doc: Document) => {
        const src = doc.file_name || doc.file_path || '';
        const ext = src.split('.').pop()?.toUpperCase();
        return ext && ext.length <= 4 ? ext : '—';
    };

    const handleSaveName = async (id: string) => {
        if (!editNameValue.trim()) { setEditingDocId(null); return; }
        try {
            await apiClient.patch(`/documents/${id}`, { file_name: editNameValue });
            setDocuments(prev => prev.map(d => d.id === id ? { ...d, file_name: editNameValue } : d));
        } catch {
            alert('Erro ao renomear o documento.');
        } finally {
            setEditingDocId(null);
        }
    };

    const trainedCount = documents.filter(d => !d.status || d.status === 'trained' || d.status === 'indexed').length;

    return (
        <div className="max-w-6xl mx-auto space-y-6">

            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Treinamento</h1>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Ensine sua IA sobre seu negócio enviando documentos e bases de conhecimento.</p>
            </div>

            {/* Stat Cards — compact horizontal */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-white dark:bg-[#111827] rounded-xl border border-gray-200 dark:border-[#1f2937] p-4 flex items-center gap-4">
                    <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                        <Database className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">Base de Conhecimento</p>
                        <p className="text-xl font-bold text-gray-900 dark:text-white">{documents.length} <span className="text-sm font-normal text-gray-400">documentos</span></p>
                    </div>
                </div>
                <div className="bg-white dark:bg-[#111827] rounded-xl border border-gray-200 dark:border-[#1f2937] p-4 flex items-center gap-4">
                    <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                        <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
                    </div>
                    <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">IA Treinada</p>
                        <p className="text-xl font-bold text-gray-900 dark:text-white">{documents.length > 0 ? 'Atualizada' : <span className="text-sm font-normal">Sem dados</span>}</p>
                    </div>
                </div>
                <div className="bg-white dark:bg-[#111827] rounded-xl border border-gray-200 dark:border-[#1f2937] p-4 flex items-center gap-4">
                    <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                        <Play className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">Processados</p>
                        <p className="text-xl font-bold text-gray-900 dark:text-white">{trainedCount} <span className="text-sm font-normal text-gray-400">indexados</span></p>
                    </div>
                </div>
            </div>

            {/* Upload Section */}
            <div className="bg-white dark:bg-[#111827] rounded-xl border border-gray-200 dark:border-[#1f2937] p-5">
                <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                    <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Destino do documento</label>
                        <select
                            value={selectedAgent}
                            onChange={(e) => setSelectedAgent(e.target.value)}
                            className="w-full bg-white dark:bg-[#0b0e14] border border-gray-300 dark:border-[#374151] rounded-lg py-2.5 px-3 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-600 focus:border-blue-600 outline-none"
                        >
                            <option value="">🌍 Base Global (todos os agentes)</option>
                            {agents.map(agent => (
                                <option key={agent.id} value={agent.id}>🤖 Apenas: {agent.name}</option>
                            ))}
                        </select>
                    </div>
                    <div className="sm:pt-6">
                        <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept=".pdf,.txt,.csv,.xlsx,.docx" />
                        <button
                            onClick={handleUploadClick}
                            disabled={uploading}
                            className="w-full sm:w-auto bg-blue-600 text-white px-5 py-2.5 rounded-lg font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                            {uploading ? 'Enviando...' : 'Enviar Documento'}
                        </button>
                    </div>
                </div>
                <p className="mt-3 text-xs text-gray-400">Formatos aceitos: PDF, TXT, CSV, XLSX, DOCX</p>
            </div>

            {/* Documents Table */}
            <div className="bg-white dark:bg-[#111827] rounded-xl border border-gray-200 dark:border-[#1f2937] overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-200 dark:border-[#1f2937] flex items-center justify-between">
                    <h2 className="text-base font-bold text-gray-900 dark:text-white">Documentos de Treinamento</h2>
                    <span className="text-xs text-gray-400">{documents.length} arquivo{documents.length !== 1 ? 's' : ''}</span>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-[#1f2937]">
                        <thead className="bg-gray-50 dark:bg-[#0b0e14]">
                            <tr>
                                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Documento</th>
                                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">Agente</th>
                                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Tipo</th>
                                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Data</th>
                                <th className="px-5 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Ações</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-[#111827] divide-y divide-gray-200 dark:divide-[#1f2937]">
                            {loading ? (
                                <tr><td colSpan={6} className="px-5 py-10 text-center"><Loader2 className="h-6 w-6 animate-spin text-blue-500 mx-auto" /></td></tr>
                            ) : documents.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-5 py-16 text-center">
                                        <BookOpen className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Nenhum documento ainda</p>
                                        <p className="text-xs text-gray-400 mt-1">Envie um PDF ou TXT para começar a treinar seus agentes.</p>
                                    </td>
                                </tr>
                            ) : documents.map((doc: any) => {
                                const matchedAgent = agents.find(a => a.embedding_namespace && a.embedding_namespace === doc.embedding_namespace);
                                return (
                                    <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-[#1a2235] transition">
                                        <td className="px-5 py-3.5">
                                            <div className="flex items-center gap-2.5">
                                                <FileText className="h-4 w-4 text-gray-400 flex-shrink-0" />
                                                {editingDocId === doc.id ? (
                                                    <div className="flex items-center gap-1.5">
                                                        <input
                                                            type="text"
                                                            value={editNameValue}
                                                            onChange={e => setEditNameValue(e.target.value)}
                                                            onKeyDown={e => { if (e.key === 'Enter') handleSaveName(doc.id); if (e.key === 'Escape') setEditingDocId(null); }}
                                                            className="bg-white dark:bg-[#0b0e14] border border-gray-300 dark:border-[#374151] rounded py-1 px-2 text-sm text-gray-900 dark:text-white outline-none w-40"
                                                            autoFocus
                                                        />
                                                        <button onClick={() => handleSaveName(doc.id)} className="text-green-500 hover:text-green-400 p-0.5"><Check className="h-4 w-4" /></button>
                                                        <button onClick={() => setEditingDocId(null)} className="text-gray-400 hover:text-gray-300 p-0.5"><X className="h-4 w-4" /></button>
                                                    </div>
                                                ) : (
                                                    <div
                                                        className="flex items-center gap-1.5 group cursor-pointer"
                                                        onClick={() => { setEditingDocId(doc.id); setEditNameValue(getDisplayName(doc)); }}
                                                        title="Clique para renomear"
                                                    >
                                                        <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate max-w-[160px] sm:max-w-xs">
                                                            {getDisplayName(doc)}
                                                        </span>
                                                        <Edit2 className="h-3 w-3 text-gray-400 opacity-0 group-hover:opacity-100 flex-shrink-0 transition-opacity" />
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-5 py-3.5 hidden sm:table-cell">
                                            <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded bg-gray-100 dark:bg-[#1f2937] text-gray-600 dark:text-gray-300">
                                                {matchedAgent ? <><span>🤖</span>{matchedAgent.name}</> : <><Globe className="h-3 w-3" />Global</>}
                                            </span>
                                        </td>
                                        <td className="px-5 py-3.5 text-xs text-gray-500 dark:text-gray-400 hidden md:table-cell">{getFileType(doc)}</td>
                                        <td className="px-5 py-3.5">
                                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                                                <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                                                Treinado
                                            </span>
                                        </td>
                                        <td className="px-5 py-3.5 text-xs text-gray-500 dark:text-gray-400 hidden lg:table-cell">{formatDate(doc.created_at)}</td>
                                        <td className="px-5 py-3.5 text-right">
                                            <button
                                                onClick={() => handleDelete(doc.id)}
                                                className="p-1.5 text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded-lg transition"
                                                title="Excluir"
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
