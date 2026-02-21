"""
Login e cadastro (empresa + primeiro usuário).
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr

from ..auth import hash_password, verify_password, create_access_token, create_refresh_token, get_current_user
from ..db import get_cursor

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    company_name: str
    email: EmailStr
    password: str
    plan: str = "free"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    with get_cursor() as cur:
        cur.execute(
            """SELECT u.id, u.tenant_id, u.password_hash, u.role, t.plan 
               FROM platform_users u 
               JOIN tenants t ON t.id = u.tenant_id
               WHERE u.email = %s""",
            (req.email,),
        )
        row = cur.fetchone()
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    
    user_id = str(row["id"])
    access_token = create_access_token(
        data={
            "sub": user_id, 
            "tenant_id": str(row["tenant_id"]),
            "role": row["role"],
            "plan": row["plan"]
        }
    )
    refresh_token = create_refresh_token(user_id)
    
    # Armazenar refresh token no banco
    with get_cursor() as cur:
        from ..config import get_settings
        import datetime
        expires = datetime.datetime.utcnow() + datetime.timedelta(days=get_settings().jwt_refresh_expire_days)
        cur.execute(
            "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
            (user_id, refresh_token, expires)
        )
        
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, background_tasks: BackgroundTasks):
    if req.plan not in ("free", "starter", "growth", "business", "enterprise"):
        req.plan = "free"
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id FROM platform_users WHERE email = %s", (req.email,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Email já cadastrado")
            cur.execute(
                """INSERT INTO tenants (company_name, plan) VALUES (%s, %s) RETURNING id""",
                (req.company_name, req.plan),
            )
            tenant_row = cur.fetchone()
            tenant_id = tenant_row["id"]
            cur.execute(
                """INSERT INTO platform_users (tenant_id, email, password_hash)
                   VALUES (%s, %s, %s) RETURNING id""",
                (tenant_id, req.email, hash_password(req.password)),
            )
            user_row = cur.fetchone()
        access_token = create_access_token(
            data={
                "sub": str(user_row["id"]), 
                "tenant_id": str(tenant_id),
                "role": "company_admin", # Primeiro usuário é admin da empresa
                "plan": req.plan
            }
        )
        refresh_token = create_refresh_token(str(user_row["id"]))
        
        with get_cursor() as cur:
            from ..config import get_settings
            import datetime
            expires = datetime.datetime.utcnow() + datetime.timedelta(days=get_settings().jwt_refresh_expire_days)
            cur.execute(
                "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (str(user_row["id"]), refresh_token, expires)
            )

        # Inject Default SPIN Selling Knowledge Base
        try:
            from ..config import get_settings
            import os, uuid
            settings = get_settings()
            spin_text = (
                "# Técnica de Vendas SPIN (SPIN Selling)\n\n"
                "A técnica SPIN ajuda a guiar o cliente através de quatro etapas focadas em fazer perguntas:\n\n"
                "1. Situação (Situation): Entender o contexto atual do cliente. Ex: 'Como você gerencia seus processos hoje?'\n"
                "2. Problema (Problem): Identificar dores e dificuldades. Ex: 'Quais são os maiores desafios que você enfrenta nesse processo?'\n"
                "3. Implicação (Implication): Aprofundar as consequências do problema. Ex: 'Como esse desafio afeta seus resultados e prejudica a operação?'\n"
                "4. Necessidade de Solução (Need-payoff): Fazer o cliente focar no valor da solução. Ex: 'Como uma ferramenta que resolve isso ajudaria sua equipe no dia a dia?'\n\n"
                "Comportamento da IA: Você deve utilizar o método SPIN para qualificar leads, investigar dores profundas antes de mostrar o produto, e conduzir negociações de forma construtiva e persuasiva. Sempre tente extrair o problema antes de dar a solução pronta."
            )
            os.makedirs(settings.upload_dir, exist_ok=True)
            safe_name = f"default_spin_{uuid.uuid4()}.txt"
            file_path = os.path.join(settings.upload_dir, safe_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(spin_text)

            file_size_mb = len(spin_text.encode('utf-8')) / (1024 * 1024)
            namespace = f"tenant_{tenant_id}"
            
            with get_cursor() as cur:
                cur.execute(
                    """INSERT INTO documents (tenant_id, file_path, file_name, file_size_mb, file_type, embedding_namespace, status)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) 
                       RETURNING id""",
                    (tenant_id, file_path, "Técnica de Vendas SPIN.txt", file_size_mb, "txt", namespace, "pending"),
                )
                doc_row = cur.fetchone()
                
            if doc_row:
                import sys
                root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                if root not in sys.path:
                    sys.path.insert(0, root)
                from execution.background_workers import process_document_task
                background_tasks.add_task(
                    process_document_task,
                    doc_id=str(doc_row["id"]),
                    file_path=file_path,
                    tenant_id=str(tenant_id),
                    embedding_namespace=namespace,
                    file_name="Técnica de Vendas SPIN.txt",
                    file_type="txt"
                )
        except Exception as e:
            print(f"Erro ao injetar arquivo SPIN: {e}")

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    except HTTPException:
        raise
    except Exception as e:
        msg = str(e).lower()
        if "72 bytes" in msg or "password" in msg:
            detail = "Erro na senha. Use uma senha com no máximo 72 caracteres."
        else:
            detail = f"Erro ao cadastrar. Verifique as tabelas (database/schema.sql). Detalhe: {e!s}"
        raise HTTPException(status_code=500, detail=detail)


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest):
    from ..auth import decode_token
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token inválido")
    
    user_id = payload["sub"]
    
    with get_cursor() as cur:
        cur.execute(
            """SELECT u.id, u.tenant_id, u.role, t.plan 
               FROM platform_users u 
               JOIN tenants t ON t.id = u.tenant_id
               JOIN refresh_tokens rt ON rt.user_id = u.id
               WHERE u.id = %s AND rt.token = %s AND rt.revoked = false AND rt.expires_at > NOW()""",
            (user_id, req.refresh_token)
        )
        row = cur.fetchone()
        
    if not row:
        raise HTTPException(status_code=401, detail="Refresh token expirado ou revogado")
        
    new_access = create_access_token(
        data={
            "sub": user_id,
            "tenant_id": str(row["tenant_id"]),
            "role": row["role"],
            "plan": row["plan"]
        }
    )
    # Podemos rotacionar o refresh token se quisermos mais segurança
    return TokenResponse(access_token=new_access, refresh_token=req.refresh_token)
