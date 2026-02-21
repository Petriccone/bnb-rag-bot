export type Locale = 'pt' | 'en' | 'es';

export interface Translations {
    // Common
    platformName: string;
    loading: string;
    cancel: string;
    save: string;
    delete: string;
    actions: string;

    // Auth
    signIn: string;
    signUp: string;
    signOut: string;
    signingIn: string;
    signingUp: string;
    email: string;
    password: string;
    fullName: string;
    signInTitle: string;
    signInSubtitle: string;
    signUpTitle: string;
    signUpSubtitle: string;
    signUpCta: string;
    orContinueWith: string;
    continueWithGoogle: string;
    continueWithApple: string;
    alreadyHaveAccount: string;
    noAccountYet: string;
    freeTrial: string;
    oauthPending: string;

    // Dashboard
    dashboardTitle: string;
    activePlan: string;
    messagesSent: string;
    tokensProcessed: string;
    vectorStorage: string;
    upgradeTitle: string;
    upgradeDescription: string;
    upgradeCta: string;
    quickActions: string;
    createNewAgent: string;
    createNewAgentDesc: string;

    // Agents
    agentsTitle: string;
    agentsDescription: string;
    newAgent: string;
    createAgentTitle: string;
    agentProfile: string;
    agentProfileDesc: string;
    agentName: string;
    agentNamePlaceholder: string;
    specialty: string;
    specialtyPlaceholder: string;
    specialtyHelp: string;
    customPrompt: string;
    customPromptPlaceholder: string;
    customPromptHelp: string;
    noAgentsFound: string;
    generalist: string;
    status: string;
    saving: string;
    saveAgent: string;
    edit: string;
    confirmDelete: string;

    // Billing
    billingTitle: string;
    billingSubtitle: string;
    manageSubscription: string;
    currentPlan: string;
    subscribeTo: string;
    contactSales: string;
    whatsIncluded: string;
    perMonth: string;

    // Nav
    navDashboard: string;
    navAgents: string;
    navTeam: string;
    navBilling: string;
    navSettings: string;
}

const pt: Translations = {
    platformName: 'Botfy',
    loading: 'Carregando...',
    cancel: 'Cancelar',
    save: 'Salvar',
    delete: 'Excluir',
    actions: 'Ações',

    signIn: 'Entrar',
    signUp: 'Cadastrar',
    signOut: 'Sair',
    signingIn: 'Entrando...',
    signingUp: 'Criando conta...',
    email: 'E-mail',
    password: 'Senha',
    fullName: 'Nome completo',
    signInTitle: 'Entre na sua conta',
    signInSubtitle: 'Gerencie seus agentes de IA em um só lugar',
    signUpTitle: 'Crie sua conta grátis',
    signUpSubtitle: 'Já tem uma conta?',
    signUpCta: 'Começar teste grátis de 14 dias',
    orContinueWith: 'ou continue com',
    continueWithGoogle: 'Continuar com Google',
    continueWithApple: 'Continuar com Apple',
    alreadyHaveAccount: 'Já tem conta?',
    noAccountYet: 'Ainda não tem conta?',
    freeTrial: 'Criar conta grátis',
    oauthPending: 'Em desenvolvimento. Para habilitar o login social, é necessário configurar credenciais OAuth do Google/Apple no backend.',

    dashboardTitle: 'Visão Geral',
    activePlan: 'Plano Ativo',
    messagesSent: 'Mensagens Enviadas',
    tokensProcessed: 'Tokens Processados',
    vectorStorage: 'Armazenamento Vetorial',
    upgradeTitle: 'Pronto para desbloquear recursos avançados?',
    upgradeDescription: 'Faça upgrade para o Pro e tenha orquestração Multi-Agente, webhooks WhatsApp PRO e até 10.000 mensagens por mês.',
    upgradeCta: 'Fazer Upgrade',
    quickActions: 'Ações Rápidas',
    createNewAgent: 'Criar Novo Agente',
    createNewAgentDesc: 'Monte personas de IA especializadas',

    agentsTitle: 'Agentes de IA',
    agentsDescription: 'Crie e gerencie seus agentes especializados. O Supervisor Botfy encaminha conversas automaticamente com base no nicho de cada agente.',
    newAgent: 'Novo Agente',
    createAgentTitle: 'Criar Agente de IA',
    agentProfile: 'Perfil do Agente',
    agentProfileDesc: 'Defina a identidade e especialização do seu novo residente Botfy.',
    agentName: 'Nome do Agente',
    agentNamePlaceholder: 'Ex: Assistente de Vendas',
    specialty: 'Especialidade (Nicho)',
    specialtyPlaceholder: 'Ex: Suporte Técnico, Qualificação de Leads',
    specialtyHelp: 'O Supervisor usa este campo para direcionar conversas corretamente.',
    customPrompt: 'Prompt Personalizado',
    customPromptPlaceholder: 'Você é um assistente que...',
    customPromptHelp: 'Substitui o comportamento padrão do orquestrador LLM.',
    noAgentsFound: 'Nenhum agente encontrado. Crie seu primeiro agente para começar.',
    generalist: 'Generalista',
    status: 'Status',
    saving: 'Salvando...',
    saveAgent: 'Salvar Agente',
    edit: 'Editar',
    confirmDelete: 'Tem certeza que deseja excluir este agente?',

    billingTitle: 'Planos e Preços',
    billingSubtitle: 'Comece grátis, depois escale a sua equipe de IA conforme o seu crescimento.',
    manageSubscription: 'Gerenciar Assinatura (Portal Stripe)',
    currentPlan: 'Plano Atual',
    subscribeTo: 'Assinar',
    contactSales: 'Falar com Vendas',
    whatsIncluded: 'O que inclui',
    perMonth: '/mês',

    navDashboard: 'Painel',
    navAgents: 'Agentes IA',
    navTeam: 'Equipe',
    navBilling: 'Assinatura',
    navSettings: 'Configurações',
};

const en: Translations = {
    platformName: 'Botfy',
    loading: 'Loading...',
    cancel: 'Cancel',
    save: 'Save',
    delete: 'Delete',
    actions: 'Actions',

    signIn: 'Sign in',
    signUp: 'Sign up',
    signOut: 'Sign out',
    signingIn: 'Signing in...',
    signingUp: 'Creating account...',
    email: 'Email address',
    password: 'Password',
    fullName: 'Full name',
    signInTitle: 'Sign in to your account',
    signInSubtitle: 'Manage your AI agents in one place',
    signUpTitle: 'Create your free account',
    signUpSubtitle: 'Already have an account?',
    signUpCta: 'Start 14-day Free Trial',
    orContinueWith: 'or continue with',
    continueWithGoogle: 'Continue with Google',
    continueWithApple: 'Continue with Apple',
    alreadyHaveAccount: 'Already have an account?',
    noAccountYet: "Don't have an account yet?",
    freeTrial: 'Create free account',
    oauthPending: 'In development. To enable social login, Google/Apple OAuth credentials must be configured in the backend.',

    dashboardTitle: 'Dashboard Overview',
    activePlan: 'Active Plan',
    messagesSent: 'Messages Sent',
    tokensProcessed: 'Tokens Processed',
    vectorStorage: 'Vector Storage',
    upgradeTitle: 'Ready to unlock advanced features?',
    upgradeDescription: 'Upgrade to Pro for Multi-Agent orchestration, WhatsApp PRO webhooks, and up to 10,000 monthly messages.',
    upgradeCta: 'Upgrade to Pro',
    quickActions: 'Quick Actions',
    createNewAgent: 'Create New Agent',
    createNewAgentDesc: 'Design specialized AI personas',

    agentsTitle: 'AI Agents',
    agentsDescription: 'Create and manage your specialized agents. The Botfy Supervisor automatically routes conversations based on each agent\'s niche.',
    newAgent: 'New Agent',
    createAgentTitle: 'Create AI Agent',
    agentProfile: 'Agent Profile',
    agentProfileDesc: 'Define the identity and specialization of your new Botfy resident.',
    agentName: 'Agent Name',
    agentNamePlaceholder: 'e.g. Sales Assistant',
    specialty: 'Specialty (Niche)',
    specialtyPlaceholder: 'e.g. Technical Support, Lead Qualification',
    specialtyHelp: 'The Supervisor uses this to route conversations properly.',
    customPrompt: 'Custom System Prompt',
    customPromptPlaceholder: 'You are a helpful assistant...',
    customPromptHelp: 'Overwrites the default behavior of the LLM Orchestrator.',
    noAgentsFound: 'No agents found. Create your first agent to get started.',
    generalist: 'Generalist',
    status: 'Status',
    saving: 'Saving...',
    saveAgent: 'Save Agent',
    edit: 'Edit',
    confirmDelete: 'Are you sure you want to delete this agent?',

    billingTitle: 'Pricing Plans',
    billingSubtitle: 'Start for free, then scale your AI workforce as you grow.',
    manageSubscription: 'Manage Subscription (Stripe Portal)',
    currentPlan: 'Current Plan',
    subscribeTo: 'Subscribe to',
    contactSales: 'Contact Sales',
    whatsIncluded: "What's included",
    perMonth: '/mo',

    navDashboard: 'Dashboard',
    navAgents: 'AI Agents',
    navTeam: 'Team',
    navBilling: 'Billing',
    navSettings: 'Settings',
};

const es: Translations = {
    platformName: 'Botfy',
    loading: 'Cargando...',
    cancel: 'Cancelar',
    save: 'Guardar',
    delete: 'Eliminar',
    actions: 'Acciones',

    signIn: 'Iniciar sesión',
    signUp: 'Registrarse',
    signOut: 'Cerrar sesión',
    signingIn: 'Iniciando sesión...',
    signingUp: 'Creando cuenta...',
    email: 'Correo electrónico',
    password: 'Contraseña',
    fullName: 'Nombre completo',
    signInTitle: 'Inicia sesión en tu cuenta',
    signInSubtitle: 'Gestiona tus agentes de IA en un solo lugar',
    signUpTitle: 'Crea tu cuenta gratis',
    signUpSubtitle: '¿Ya tienes una cuenta?',
    signUpCta: 'Comenzar prueba gratis de 14 días',
    orContinueWith: 'o continúa con',
    continueWithGoogle: 'Continuar con Google',
    continueWithApple: 'Continuar con Apple',
    alreadyHaveAccount: '¿Ya tienes cuenta?',
    noAccountYet: '¿Aún no tienes cuenta?',
    freeTrial: 'Crear cuenta gratis',
    oauthPending: 'En desarrollo. Para habilitar el inicio de sesión social, es necesario configurar las credenciales OAuth de Google/Apple en el backend.',

    dashboardTitle: 'Panel General',
    activePlan: 'Plan Activo',
    messagesSent: 'Mensajes Enviados',
    tokensProcessed: 'Tokens Procesados',
    vectorStorage: 'Almacenamiento Vectorial',
    upgradeTitle: '¿Listo para desbloquear funciones avanzadas?',
    upgradeDescription: 'Actualiza a Pro para orquestación Multi-Agente, webhooks WhatsApp PRO y hasta 10,000 mensajes mensuales.',
    upgradeCta: 'Actualizar a Pro',
    quickActions: 'Acciones Rápidas',
    createNewAgent: 'Crear Nuevo Agente',
    createNewAgentDesc: 'Diseña personas de IA especializadas',

    agentsTitle: 'Agentes de IA',
    agentsDescription: 'Crea y gestiona tus agentes especializados. El Supervisor Botfy enruta automáticamente las conversaciones según el nicho de cada agente.',
    newAgent: 'Nuevo Agente',
    createAgentTitle: 'Crear Agente de IA',
    agentProfile: 'Perfil del Agente',
    agentProfileDesc: 'Define la identidad y especialización de tu nuevo residente Botfy.',
    agentName: 'Nombre del Agente',
    agentNamePlaceholder: 'Ej: Asistente de Ventas',
    specialty: 'Especialidad (Nicho)',
    specialtyPlaceholder: 'Ej: Soporte Técnico, Calificación de Leads',
    specialtyHelp: 'El Supervisor usa esto para dirigir conversaciones correctamente.',
    customPrompt: 'Prompt Personalizado',
    customPromptPlaceholder: 'Eres un asistente que...',
    customPromptHelp: 'Reemplaza el comportamiento predeterminado del orquestador LLM.',
    noAgentsFound: 'No se encontraron agentes. Crea tu primer agente para comenzar.',
    generalist: 'Generalista',
    status: 'Estado',
    saving: 'Guardando...',
    saveAgent: 'Guardar Agente',
    edit: 'Editar',
    confirmDelete: '¿Estás seguro de que deseas eliminar este agente?',

    billingTitle: 'Planes y Precios',
    billingSubtitle: 'Comienza gratis, luego escala tu equipo de IA según crezcas.',
    manageSubscription: 'Gestionar Suscripción (Portal Stripe)',
    currentPlan: 'Plan Actual',
    subscribeTo: 'Suscribirse a',
    contactSales: 'Contactar Ventas',
    whatsIncluded: 'Qué incluye',
    perMonth: '/mes',

    navDashboard: 'Panel',
    navAgents: 'Agentes IA',
    navTeam: 'Equipo',
    navBilling: 'Suscripción',
    navSettings: 'Configuración',
};

export const translations: Record<Locale, Translations> = { pt, en, es };

export const localeNames: Record<Locale, string> = {
    pt: 'Português',
    en: 'English',
    es: 'Español',
};

export const localeFlags: Record<Locale, string> = {
    pt: '🇧🇷',
    en: '🇺🇸',
    es: '🇪🇸',
};
