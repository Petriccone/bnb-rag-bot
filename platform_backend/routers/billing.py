"""
Gerenciamento de cobrança, Checkout e Webhook do Stripe.
"""
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Optional

from ..dependencies import get_current_user
from ..config import get_settings
from ..db import get_cursor

router = APIRouter(prefix="/billing", tags=["billing"])

settings = get_settings()
stripe.api_key = settings.stripe_secret_key

class CheckoutRequest(BaseModel):
    plan: str  # 'starter', 'growth', 'business', 'enterprise'
    success_url: str
    cancel_url: str

@router.post("/create-checkout-session")
def create_checkout_session(req: CheckoutRequest, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant")

    # Busca ou cria customer no Stripe
    with get_cursor() as cur:
        cur.execute("SELECT stripe_customer_id, company_name, email FROM tenants t JOIN platform_users u ON u.tenant_id = t.id WHERE t.id = %s LIMIT 1", (tenant_id,))
        row = cur.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")

    customer_id = row.get("stripe_customer_id")
    if not customer_id:
        customer = stripe.Customer.create(
            email=row["email"],
            name=row["company_name"],
            metadata={"tenant_id": tenant_id}
        )
        customer_id = customer.id
        with get_cursor() as cur:
            cur.execute("UPDATE tenants SET stripe_customer_id = %s WHERE id = %s", (customer_id, tenant_id))

    if req.plan == "starter":
        price_id = settings.stripe_starter_price_id
    elif req.plan == "growth":
        price_id = settings.stripe_growth_price_id
    elif req.plan == "business":
        price_id = settings.stripe_business_price_id
    elif req.plan == "enterprise":
        price_id = settings.stripe_enterprise_price_id
    else:
        raise HTTPException(status_code=400, detail="Plano inválido")

    if not price_id:
        raise HTTPException(status_code=400, detail=f"Price ID para plano {req.plan} não configurado.")

    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=req.success_url,
            cancel_url=req.cancel_url,
            metadata={"tenant_id": tenant_id, "plan": req.plan}
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portal")
def create_portal_session(return_url: str, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    with get_cursor() as cur:
        cur.execute("SELECT stripe_customer_id FROM tenants WHERE id = %s", (tenant_id,))
        row = cur.fetchone()
    
    if not row or not row.get("stripe_customer_id"):
        raise HTTPException(status_code=400, detail="Nenhuma conta de cobrança encontrada.")

    session = stripe.billing_portal.Session.create(
        customer=row["stripe_customer_id"],
        return_url=return_url,
    )
    return {"portal_url": session.url}

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook Error: {e}")

    # Handle events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        tenant_id = session.get('metadata', {}).get('tenant_id')
        plan = session.get('metadata', {}).get('plan')
        subscription_id = session.get('subscription')
        
        if tenant_id and plan:
            with get_cursor() as cur:
                cur.execute(
                    "UPDATE tenants SET plan = %s, stripe_subscription_id = %s, updated_at = NOW() WHERE id = %s",
                    (plan, subscription_id, tenant_id)
                )

    elif event['type'] in ['customer.subscription.updated', 'customer.subscription.deleted']:
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        status = subscription.get('status')
        
        # Se cancelado ou inadimplente, talvez queira fazer downgrade
        if event['type'] == 'customer.subscription.deleted' or status in ['unpaid', 'canceled']:
            with get_cursor() as cur:
                cur.execute(
                    "UPDATE tenants SET plan = 'free', stripe_subscription_id = NULL, updated_at = NOW() WHERE stripe_customer_id = %s",
                    (customer_id,)
                )

    return {"status": "success"}
