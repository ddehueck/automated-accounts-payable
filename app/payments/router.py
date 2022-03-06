from datetime import datetime, timedelta

import stripe
from fastapi import APIRouter, Depends, Form, Request
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Header
from fastapi.responses import HTMLResponse, RedirectResponse
from loguru import logger as log
from starlette import status
from starlette.responses import JSONResponse
from starlette.status import HTTP_302_FOUND

import app.db.models as db_models
from app.auth.utils import requires_authentication
from app.config import config as global_config
from app.db.session import SessionLocal
from app.frontend.templates import template_response
from app.users.db_utils import get_user_by_id

from .config import config
from .db_utils import update_user_payment_plan

router = APIRouter()
stripe.api_key = config.stripe_secret_key


@router.get("/select-plan", response_class=HTMLResponse)
async def get_select_plan(request: Request, user_id: int = Depends(requires_authentication)):
    return template_response("./payments/select-plan.html", {"request": request})


@router.get("/subscriptions/success", response_class=HTMLResponse)
async def get_subscriptions_success(
    request: Request, plan: str, session_id: str, user_id: str = Depends(requires_authentication)
):
    with SessionLocal() as db:
        update_user_payment_plan(db, user_id, plan, session_id)
    return template_response("./payments/success.html", {"request": request})


@router.get("/subscriptions/cancel", response_class=HTMLResponse)
async def get_subscriptions_cancel(request: Request, user_id: str = Depends(requires_authentication)):
    return template_response("./payments/cancelled.html", {"request": request})


@router.post("/create-checkout-session", response_class=RedirectResponse)
async def get_checkout(plan_key: str = Form(...), user_id: int = Depends(requires_authentication)):
    if plan_key == "free":
        return RedirectResponse("/home", status_code=HTTP_302_FOUND)
    try:
        prices = stripe.Price.list()

        log.debug(f"PRICEs, {prices}, KEY {plan_key}")

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": prices.data[0].id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=global_config.base_domain
            + f"/subscriptions/success?plan={plan_key}"
            + "&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=global_config.base_domain + "/subscriptions/cancel",
        )

        # TODO save session_id to user table?

        return RedirectResponse(checkout_session.url, status_code=303)
    except Exception as e:
        log.exception(e)
        return JSONResponse({"error": "An unknown error occured"}, status_code=500)


@router.post("/create-portal-session", response_class=RedirectResponse)
async def customer_portal(user_id: int = Depends(requires_authentication)):
    # For demonstration purposes, we're using the Checkout session to retrieve the customer ID.
    # Typically this is stored alongside the authenticated user in your database.
    with SessionLocal() as db:
        user = get_user_by_id(db, user_id)

    checkout_session = stripe.checkout.Session.retrieve(user.stripe_session_id)

    portalSession = stripe.billing_portal.Session.create(
        customer=checkout_session.customer,
        return_url=global_config.base_domain,  # Redirect back to home/dashboard
    )
    return RedirectResponse(portalSession.url, status_code=303)


@router.post("/stripe-webhook", response_class=JSONResponse)
async def webhook_received(request: Request, signature: str = Header(None, alias="stripe-signature")):
    # Replace this endpoint secret with your endpoint's unique secret
    # If you are testing with the CLI, find the secret by running 'stripe listen'
    # If you are using an endpoint defined with the API or dashboard, look in your webhook settings
    # at https://dashboard.stripe.com/webhooks
    request_json = await request.json()

    if config.stripe_webhook_secret:
        try:
            event = stripe.Webhook.construct_event(
                payload=request_json, sig_header=signature, secret=config.stripe_webhook_secret
            )
            data = event["data"]
        except Exception as e:
            return e
        # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event["type"]
    else:
        data = request_json["data"]
        event_type = request_json["type"]
    data_object = data["object"]

    log.debug(f"stripe event:  {event_type}")

    if event_type == "checkout.session.completed":
        print("🔔 Payment succeeded!")

    elif event_type == "customer.subscription.trial_will_end":
        print("Subscription trial will end")

    elif event_type == "customer.subscription.created":
        print("Subscription created %s", event.id)

    elif event_type == "customer.subscription.updated":
        print("Subscription updated %s", event.id)

    elif event_type == "customer.subscription.deleted":
        # handle subscription cancelled automatically based
        # upon your subscription settings. Or if the user cancels it.
        print("Subscription canceled: %s", event.id)

    return JSONResponse({"status": "success"})
