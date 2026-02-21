"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useI18n } from '@/lib/i18n-context';
import { BookOpen, Upload, Database, CheckCircle, Play, FileText, Trash2, Loader2, Edit2, Check, X } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Document {
    id: string;
    file_path: string;
    created_at: string;
    status?: string;
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

    useEffect(() => {
        fetchDocumentsAndAgents();
    }, []);

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        try {
            setUploading(true);

            // Check if we need to assign or create a namespace for the selected agent
            let namespace = '';
            if (selectedAgent) {
                const agent = agents.find(a => a.id === selectedAgent);
                if (agent) {
                    namespace = agent.embedding_namespace;
                    if (!namespace) {
                        // Se o agente não tinha namespace, criamos um e atualizamos o agente
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

            const response = await apiClient.post(uploadUrl, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            if (response.status === 200 || response.status === 201) {
                // Refresh list
                await fetchDocumentsAndAgents();
            } else {
                console.error("Failed to upload document");
                alert("Erro ao enviar o documento.");
            }
        } catch (error) {
            console.error('Error uploading document:', error);
            alert("Erro ao enviar o documento.");
        } finally {
            setUploading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Tem certeza que deseja remover este documento?")) return;

        try {
            const response = await apiClient.delete(`/documents/${id}`);
            if (response.status === 200) {
                setDocuments(prev => prev.filter(doc => doc.id !== id));
            } else {
                alert("Erro ao remover documento.");
            }
        } catch (error) {
            console.error('Error deleting document', error);
        }
    };

    const formatDate = (dateString: string) => {
        try {
            return new Date(dateString).toLocaleDateString('pt-BR');
        } catch {
            return dateString;
        }
    };

    const getFileName = (path: string) => {
        if (!path) return 'Documento';
        const parts = path.split('/');
        return parts[parts.length - 1];
    };

    const getFileType = (path: string) => {
        if (!path) return 'N/A';
        const parts = path.split('.');
        return parts.length > 1 ? parts[parts.length - 1].toUpperCase() : 'N/A';
    };

    const handleSaveName = async (id: string) => {
        if (!editNameValue.trim()) {
            setEditingDocId(null);
            return;
        }
        try {
            await apiClient.patch(`/documents/${id}`, { file_name: editNameValue });
            // Update UI optimistically or fetch
            setDocuments(prev => prev.map(d => d.id === id ? { ...d, file_path: editNameValue } : d));
        } catch (error) {
            console.error('Error renaming document', error);
            alert("Erro ao renomear o documento.");
        } finally {
            setEditingDocId(null);
        }
    };

    return (
        <div className="max-w-6xl mx-auto">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white transition-colors duration-200">Treinamento</h1>
                    <p className="text-gray-500 dark:text-gray-400 transition-colors duration-200">Ensine sua IA sobre seu negócio enviando documentos e bases de conhecimento.</p>
                </div>
                <div className="flex items-center space-x-4">
                    <select
                        value={selectedAgent}
                        onChange={(e) => setSelectedAgent(e.target.value)}
                        className="bg-white dark:bg-[#0b0e14] border border-gray-300 dark:border-[#374151] rounded-lg py-2 px-3 text-sm text-gray-900 dark:text-white transition-colors duration-200 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
                    >
                        <option value="">Base Global (Lida por TODOS os Agentes)</option>
                        {agents.map(agent => (
                            <option key={agent.id} value={agent.id}>
                                Apenas para o Agente: {agent.name}
                            </option>
                        ))}
                    </select>

                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileChange}
                        className="hidden"
                        accept=".pdf,.txt,.csv,.xlsx,.docx"
                    />
                    <button
                        onClick={handleUploadClick}
                        disabled={uploading}
                        className="bg-blue-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-blue-700 transition flex items-center shadow-sm disabled:opacity-50 min-w-max"
                    >
                        {uploading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Upload className="h-4 w-4 mr-2" />}
                        {uploading ? 'Enviando...' : 'Enviar Documento'}
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white dark:bg-[#111827] p-6 shadow rounded-xl border border-gray-200 dark:border-[#1f2937] transition-colors duration-200">
                    <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center mb-4 transition-colors duration-200">
                        <Database className="h-6 w-6 text-blue-600 dark:text-blue-400 transition-colors duration-200" />
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white transition-colors duration-200">Base de Conhecimento</h3>
                    <p className="text-gray-500 dark:text-gray-400 text-sm mt-1 transition-colors duration-200">{documents.length} documentos indexados</p>
                </div>
                <div className="bg-white dark:bg-[#111827] p-6 shadow rounded-xl border border-gray-200 dark:border-[#1f2937] transition-colors duration-200">
                    <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center mb-4 transition-colors duration-200">
                        <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400 transition-colors duration-200" />
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white transition-colors duration-200">IA Treinada</h3>
                    <p className="text-gray-500 dark:text-gray-400 text-sm mt-1 transition-colors duration-200">Status: {documents.length > 0 ? 'Atualizada' : 'Sem dados'}</p>
                </div>
                <div className="bg-white dark:bg-[#111827] p-6 shadow rounded-xl border border-gray-200 dark:border-[#1f2937] transition-colors duration-200">
                    <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center mb-4 transition-colors duration-200">
                        <Play className="h-6 w-6 text-purple-600 dark:text-purple-400 transition-colors duration-200" />
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white transition-colors duration-200">Sessões de Treino</h3>
                    <p className="text-gray-500 dark:text-gray-400 text-sm mt-1 transition-colors duration-200">Automático</p>
                </div>
            </div>

            <div className="bg-white dark:bg-[#111827] shadow rounded-xl border border-gray-200 dark:border-[#1f2937] overflow-hidden transition-colors duration-200">
                <div className="p-6 border-b border-gray-200 dark:border-[#1f2937] transition-colors duration-200">
                    <h2 className="text-lg font-bold text-gray-900 dark:text-white transition-colors duration-200">Documentos de Treinamento</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-[#1f2937] transition-colors duration-200">
                        <thead className="bg-gray-50 dark:bg-[#0b0e14] transition-colors duration-200">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Documento</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Agente</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tipo</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Data</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Ações</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-[#111827] divide-y divide-gray-200 dark:divide-[#1f2937] transition-colors duration-200">
                            {loading ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                                        Carregando documentos...
                                    </td>
                                </tr>
                            ) : documents.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                                        Nenhum documento encontrado.
                                    </td>
                                </tr>
                            ) : documents.map((doc: any) => {
                                const matchedAgent = agents.find(a => a.embedding_namespace === doc.embedding_namespace);
                                const agentName = matchedAgent ? matchedAgent.name : "Base Geral";
                                return (
                                    <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-[#1f2937] transition">
                                        <td className="px-6 py-4 flex items-center">
                                            <FileText className="h-5 w-5 text-gray-400 mr-3" />
                                            {editingDocId === doc.id ? (
                                                <div className="flex items-center space-x-2">
                                                    <input
                                                        type="text"
                                                        value={editNameValue}
                                                        onChange={e => setEditNameValue(e.target.value)}
                                                        className="bg-white dark:bg-[#0b0e14] border border-gray-300 dark:border-[#374151] rounded py-1 px-2 text-sm text-gray-900 dark:text-white"
                                                        autoFocus
                                                    />
                                                    <button onClick={() => handleSaveName(doc.id)} className="text-green-500 hover:text-green-400 p-1">
                                                        <Check className="h-4 w-4" />
                                                    </button>
                                                    <button onClick={() => setEditingDocId(null)} className="text-gray-500 hover:text-gray-400 p-1">
                                                        <X className="h-4 w-4" />
                                                    </button>
                                                </div>
                                            ) : (
                                                <div className="flex items-center group cursor-pointer" onClick={() => { setEditingDocId(doc.id); setEditNameValue(getFileName(doc.file_path)); }}>
                                                    <span className="text-sm font-medium text-gray-900 dark:text-gray-200 truncate max-w-xs transition-colors duration-200" title={getFileName(doc.file_path)}>
                                                        {getFileName(doc.file_path)}
                                                    </span>
                                                    <Edit2 className="h-3 w-3 text-gray-400 opacity-0 group-hover:opacity-100 ml-2 transition-opacity" />
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 transition-colors duration-200">
                                            <span className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded text-xs">{agentName}</span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 transition-colors duration-200">{getFileType(doc.file_path)}</td>
                                        <td className="px-6 py-4">
                                            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 border border-transparent dark:border-green-800/50 transition-colors duration-200">
                                                Treinado
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 transition-colors duration-200">{formatDate(doc.created_at)}</td>
                                        <td className="px-6 py-4 text-right text-sm font-medium">
                                            <button
                                                onClick={() => handleDelete(doc.id)}
                                                className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 p-1 rounded hover:bg-red-50 dark:hover:bg-red-400/10 transition"
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
