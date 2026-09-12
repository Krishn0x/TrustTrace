import os
import sys
import asyncio
import base64
from algosdk import account, encoding, mnemonic

from dotenv import load_dotenv

# Load local environment variables from .env
# This keeps secrets out of your terminal history and Git.
load_dotenv()

from x402 import x402Client, x402ClientConfig
from x402.mechanisms.avm.signer import ClientAvmSigner
from x402.mechanisms.avm.exact.register import register_exact_avm_client
from x402.mechanisms.avm.constants import ALGORAND_TESTNET_CAIP2

class TestnetSigner(ClientAvmSigner):
    def __init__(self, private_key: str):
        self.private_key = private_key
        self._address = account.address_from_private_key(private_key)
        
    @property
    def address(self) -> str:
        return self._address
        
    def sign_transactions(self, unsigned_txns: list[bytes], indexes_to_sign: list[int]) -> list[bytes | None]:
        signed = []
        for i, txn_bytes in enumerate(unsigned_txns):
            if i in indexes_to_sign:
                b64_encoded = base64.b64encode(txn_bytes).decode("utf-8")
                unsigned_txn = encoding.msgpack_decode(b64_encoded)
                signed_txn = unsigned_txn.sign(self.private_key)
                signed_b64 = encoding.msgpack_encode(signed_txn)
                signed.append(base64.b64decode(signed_b64))
            else:
                signed.append(None)
        return signed

async def run_e2e_test():
    pk = os.environ.get("X402_CLIENT_PRIVATE_KEY")
    mnemo = os.environ.get("X402_CLIENT_MNEMONIC")
    
    if mnemo:
        # Normalize: replace commas/newlines with spaces
        mnemo = mnemo.replace(',', ' ').replace('\n', ' ').replace('\r', ' ')
        words = mnemo.strip().split()
        mnemo = ' '.join(words)
        
        if len(words) == 24:
            # Pera Universal Wallet (BIP-39 -> SLIP-0010 m/44'/283'/0'/0'/0')
            try:
                from mnemonic import Mnemonic
                import hmac
                import hashlib
                from nacl.signing import SigningKey
                
                m = Mnemonic("english")
                if not m.check(mnemo):
                    raise ValueError("Invalid BIP-39 checksum")
                
                seed = m.to_seed(mnemo)
                I = hmac.new(b"ed25519 seed", seed, hashlib.sha512).digest()
                key, chain_code = I[:32], I[32:]
                
                # Derivation path: m/44'/283'/0'/0'/0' (All hardened for Ed25519)
                for p in [44, 283, 0, 0, 0]:
                    data = b'\x00' + key + (p + 0x80000000).to_bytes(4, 'big')
                    I = hmac.new(chain_code, data, hashlib.sha512).digest()
                    key, chain_code = I[:32], I[32:]
                    
                sk = SigningKey(key)
                pk_bytes = key + sk.verify_key.encode()
                pk = base64.b64encode(pk_bytes).decode("utf-8")
            except Exception as e:
                print(f"FAIL: Provided 24-word X402_CLIENT_MNEMONIC is invalid ({e}).")
                sys.exit(1)
        elif len(words) == 25:
            # Algorand Legacy Wallet
            try:
                pk = mnemonic.to_private_key(mnemo)
            except Exception as e:
                print(f"FAIL: Provided 25-word X402_CLIENT_MNEMONIC is invalid ({e}).")
                sys.exit(1)
        else:
            print(f"FAIL: Mnemonic has {len(words)} words. Expected 24 or 25.")
            sys.exit(1)
            
    if not pk:
        print("FAIL: No wallet credential found.")
        print("Please configure X402_CLIENT_MNEMONIC (25-word phrase) in your backend/.env file.")
        print("DO NOT commit the .env file.")
        sys.exit(1)
        
    try:
        signer = TestnetSigner(pk)
    except Exception:
        print("FAIL: Failed to initialize signer. Ensure your credential is valid.")
        sys.exit(1)
        
    if not encoding.is_valid_address(signer.address):
        print("FAIL: Derived address from private key is invalid.")
        sys.exit(1)
        
    avm_address = os.environ.get("AVM_ADDRESS")
    if avm_address and signer.address != avm_address:
        print("FAIL: Wallet credential does not correspond to AVM_ADDRESS.")
        print("Please ensure AVM_ADDRESS matches the public address of your configured mnemonic.")
        sys.exit(1)
        
    print(f"--- Client Signer Initialized ---")
    print(f"Client Address: {signer.address}")
    
    from x402.http import x402HTTPClient
    import httpx
    
    # Initialize the client
    client = x402Client(x402ClientConfig())
    register_exact_avm_client(client, signer, networks=[ALGORAND_TESTNET_CAIP2])
    x402_http_client = x402HTTPClient(client)
    
    print("--- Requesting Protected Endpoint ---")
    try:
        url = "http://localhost:8000/x402/paid-analysis/1"
        async with httpx.AsyncClient() as http_client:
            res = await http_client.get(url)
            
            if res.status_code == 402:
                print("Status: 402 Payment Required")
                # Parse 402, create payment payload, get headers
                retry_headers, payload = await x402_http_client.handle_402_response(
                    headers=dict(res.headers),
                    body=res.content
                )
                print(f"Payment Required: Yes")
                print(f"Selected Network: {getattr(payload, 'network', 'Unknown')}")
                print(f"Constructed Payment Payload for Amount: {getattr(payload, 'amount', 'Unknown')}")
                print(f"Receiver Address (payTo): {getattr(payload, 'pay_to', 'Unknown')}")
                
                print("--- Submitting Payment / Proof ---")
                res = await http_client.get(url, headers=retry_headers)
                
            print("--- Final Result ---")
            print("Status:", res.status_code)
            
            if res.status_code == 200:
                data = res.json()
                print("Successfully retrieved protected analysis!")
                print(f"Compromised Service: {data.get('result', {}).get('compromised_service', {}).get('name')}")
                print(f"Affected Count: {data.get('result', {}).get('affected_count')}")
                print(f"Summary: {data.get('result', {}).get('summary')}")
            else:
                print("Failed to retrieve analysis:", res.text)
            
    except Exception as e:
        print("Exception during fetch:", str(e))
        
    print("\n--- Fake Payment Rejection Test ---")
    async with httpx.AsyncClient() as http_client:
        fake_res = await http_client.get("http://localhost:8000/x402/paid-analysis/1", headers={"x-payment": "FAKE_BASE64_HEADER_aGFja2Vy"})
        print("Fake Payment Status:", fake_res.status_code)
        if fake_res.status_code >= 400:
            print("Fake payment correctly rejected.")
        else:
            print("FAIL: Fake payment was accepted!")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
