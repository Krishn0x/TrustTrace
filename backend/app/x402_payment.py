import os
from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .database import get_db
from .graph_engine import simulate_compromise
from . import schemas

# x402 SDK Imports
from x402 import (
    x402ResourceServer, Price, FacilitatorConfig, PaymentRequirements, 
    parse_payment_payload
)
from x402.http import HTTPFacilitatorClient, safe_base64_decode

# AVM imports
from x402.mechanisms.avm.exact.register import register_exact_avm_server
from x402.mechanisms.avm.constants import ALGORAND_TESTNET_CAIP2, AVM_ADDRESS_REGEX
import re

router = APIRouter()

AVM_ADDRESS = os.environ.get("AVM_ADDRESS", "DEMO_WALLET_ADDRESS")
FACILITATOR_URL = os.environ.get("FACILITATOR_URL", "https://facilitator.goplausible.xyz")

if AVM_ADDRESS != "DEMO_WALLET_ADDRESS" and not re.match(AVM_ADDRESS_REGEX, AVM_ADDRESS):
    raise ValueError(f"Invalid Algorand address format for AVM_ADDRESS: {AVM_ADDRESS}")

# Configure Facilitator and Resource Server
_fac_client = HTTPFacilitatorClient(FacilitatorConfig(url=FACILITATOR_URL))
x402_server = x402ResourceServer(facilitator_clients=[_fac_client])
register_exact_avm_server(x402_server)
_server_initialized = False

async def get_x402_server():
    global _server_initialized
    if not _server_initialized:
        x402_server.initialize()
        _server_initialized = True
    return x402_server

def get_trusttrace_requirements() -> PaymentRequirements:
    return PaymentRequirements(
        network=ALGORAND_TESTNET_CAIP2,
        scheme="exact",
        asset="ALGO",
        amount="0.001",
        payTo=AVM_ADDRESS,
        description="TrustTrace blast radius analysis",
        maxTimeoutSeconds=3600
    )

@router.get("/paid-analysis/{service_id}")
async def paid_analysis(
    service_id: int, 
    request: Request,
    db: Session = Depends(get_db)
):
    server = await get_x402_server()
    requirements = get_trusttrace_requirements()
    
    payment_header = request.headers.get("x-payment")
    
    if not payment_header:
        # Return genuine 402 with x402 payment requirements
        payment_required = server.create_payment_required_response(requirements=[requirements])
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=payment_required.model_dump(by_alias=True, exclude_none=True),
            headers={"x-payment-required": "true"}
        )
        
    # Process genuine payment
    try:
        # Decode base64 payload from x-payment header
        payload_bytes = safe_base64_decode(payment_header)
        payload = parse_payment_payload(payload_bytes)
        
        # Verify via facilitator
        verify_result = await server.verify_payment(payload, requirements)
        
        if not verify_result.success:
            raise HTTPException(status_code=403, detail="Payment verification failed")
            
        # Optional: Settle payment via facilitator
        await server.settle_payment(payload, requirements)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payment: {str(e)}")

    # Executing actual TrustTrace analysis after verification
    try:
        service, affected, summary = simulate_compromise(db, service_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))

    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for item in affected:
        counts[item["severity"]] = counts.get(item["severity"], 0) + 1

    return {
        "status": "success",
        "result": {
            "compromised_service": {
                "id": service.id,
                "name": service.name,
                "service_type": service.service_type,
            },
            "affected_count": len(affected),
            "severity_counts": counts,
            "affected_services": affected,
            "summary": summary
        }
    }

@router.get("/demo-agent/{service_id}")
async def demo_agent(service_id: int, db: Session = Depends(get_db)):
    """
    PRESERVED MOCK DEMO FLOW
    This is separated from the REAL x402 flow above to preserve the UI demo functionality
    without compromising the security of the actual endpoint.
    """
    server = await get_x402_server()
    requirements = get_trusttrace_requirements()
    
    # 1. Generate real requirements for demo display
    payment_required = server.create_payment_required_response(requirements=[requirements])
    
    step1 = {
        "step": 1,
        "action": "Agent requests analysis (REAL 402 generated)",
        "response": {
            "status": 402,
            "detail": payment_required.model_dump(by_alias=True, exclude_none=True)
        }
    }
    
    step2 = {
        "step": 2,
        "action": "Agent creates mock payload (Configuration Missing)",
        "token": "MOCK_PAYLOAD_BECAUSE_TESTNET_CREDENTIALS_MISSING"
    }

    step3 = {
        "step": 3,
        "action": "Payment verification skipped (Demo Fallback)",
        "verified": True
    }

    try:
        service, affected, summary = simulate_compromise(db, service_id)
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for item in affected:
            counts[item["severity"]] = counts.get(item["severity"], 0) + 1
            
        step4 = {
            "step": 4,
            "action": "Analysis unlocked via fallback",
            "result": {
                "compromised_service": {
                    "id": service.id,
                    "name": service.name,
                    "service_type": service.service_type,
                },
                "affected_count": len(affected),
                "severity_counts": counts,
                "affected_services": affected,
                "summary": summary
            }
        }
    except ValueError as error:
        step4 = {
            "step": 4,
            "action": "Analysis unlocked but failed",
            "error": str(error)
        }

    return {
        "steps": [step1, step2, step3, step4]
    }
