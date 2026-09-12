import os
import sys
import asyncio
import base64
import hashlib
import hmac
import nacl.bindings
from nacl.signing import SigningKey
from algosdk import account, encoding, mnemonic
from algosdk.transaction import SignedTransaction

from dotenv import load_dotenv

# Load local environment variables from .env
# This keeps secrets out of your terminal history and Git.
load_dotenv()

from x402 import x402Client, x402ClientConfig
from x402.mechanisms.avm.signer import ClientAvmSigner
from x402.mechanisms.avm.exact.register import register_exact_avm_client
from x402.mechanisms.avm.constants import ALGORAND_TESTNET_CAIP2

def sha512(d): return hashlib.sha512(d).digest()
def sha256(d): return hashlib.sha256(d).digest()
def hmac_sha512(key, msg): return hmac.new(key, msg, hashlib.sha512).digest()

class TestnetSigner(ClientAvmSigner):
    def __init__(self, private_key: str = None, kl: bytes = None, kr: bytes = None, pk: bytes = None):
        self.private_key = private_key
        self.kl = kl
        self.kr = kr
        self.pk = pk
        
        if private_key:
            self._address = account.address_from_private_key(private_key)
        else:
            self._address = encoding.encode_address(pk)
        
    @property
    def address(self) -> str:
        return self._address
        
    def sign_transactions(self, unsigned_txns: list[bytes], indexes_to_sign: list[int]) -> list[bytes | None]:
        signed = []
        for i, txn_bytes in enumerate(unsigned_txns):
            if i in indexes_to_sign:
                b64_encoded = base64.b64encode(txn_bytes).decode("utf-8")
                unsigned_txn = encoding.msgpack_decode(b64_encoded)
                
                if self.private_key:
                    signed_txn = unsigned_txn.sign(self.private_key)
                else:
                    msg = unsigned_txn.bytes_to_sign()
                    r = nacl.bindings.crypto_core_ed25519_scalar_reduce(sha512(self.kr + msg))
                    R = nacl.bindings.crypto_scalarmult_ed25519_base_noclamp(r)
                    h = nacl.bindings.crypto_core_ed25519_scalar_reduce(sha512(R + self.pk + msg))
                    mulResult = nacl.bindings.crypto_core_ed25519_scalar_mul(h, self.kl)
                    S = nacl.bindings.crypto_core_ed25519_scalar_add(r, mulResult)
                    sig = R + S
                    signed_txn = SignedTransaction(unsigned_txn, base64.b64encode(sig).decode())
                    
                signed_b64 = encoding.msgpack_encode(signed_txn)
                signed.append(base64.b64decode(signed_b64))
            else:
                signed.append(None)
        return signed

def derive_pera_24_word(mnemo_str: str, avm_address: str):
    from mnemonic import Mnemonic
    m = Mnemonic("english")
    if not m.check(mnemo_str):
        raise ValueError("Invalid BIP-39 checksum")
    seed = m.to_seed(mnemo_str, passphrase="")
    
    # fromSeed logic
    k = sha512(seed)
    kl = bytearray(k[:32])
    kr = bytearray(k[32:])
    while (kl[31] & 0x20) != 0:
        k = hmac_sha512(kl, kr)
        kl = bytearray(k[:32])
        kr = bytearray(k[32:])
    
    kl[0] &= 0xF8
    kl[31] &= 0x7F
    kl[31] |= 0x40
    c = sha256(b"\x01" + seed)
    root_key = bytes(kl) + bytes(kr) + c

    def derive_hardened(kL, kR, cc, idx):
        idx_b = idx.to_bytes(4, 'little')
        z = hmac_sha512(cc, b"\x00" + kL + kR + idx_b)
        child_cc = hmac_sha512(cc, b"\x01" + kL + kR + idx_b)
        return z, child_cc

    def derive_non_hardened(kL, cc, idx):
        idx_b = idx.to_bytes(4, 'little')
        pk_noclamp = nacl.bindings.crypto_scalarmult_ed25519_base_noclamp(kL)
        z = hmac_sha512(cc, b"\x02" + pk_noclamp + idx_b)
        child_cc = hmac_sha512(cc, b"\x03" + pk_noclamp + idx_b)
        return z, child_cc

    def derive_child(ext_key, idx):
        kL, kR, cc = ext_key[:32], ext_key[32:64], ext_key[64:96]
        if idx >= 0x80000000:
            z, child_cc = derive_hardened(kL, kR, cc, idx)
        else:
            z, child_cc = derive_non_hardened(kL, cc, idx)
            
        zl = bytearray(z[:32])
        zr = z[32:]
        # Peikert (g=9)
        zl[31] = 0
        zl[30] &= 0x7F
        
        left = int.from_bytes(kL, 'little') + int.from_bytes(zl, 'little') * 8
        if left >= 2**255: raise Exception("overflow")
        right = (int.from_bytes(kR, 'little') + int.from_bytes(zr, 'little')) % (2**256)
        
        return left.to_bytes(32, 'little') + right.to_bytes(32, 'little') + child_cc[32:]

    # Search accounts 0..9
    for i in range(10):
        for j in range(10):
            # m/44'/283'/i'/0/j
            path = [44 + 0x80000000, 283 + 0x80000000, i + 0x80000000, 0, j]
            curr = root_key
            for p in path:
                curr = derive_child(curr, p)
            kL = curr[:32]
            kR = curr[32:64]
            pk = nacl.bindings.crypto_scalarmult_ed25519_base_noclamp(kL)
            addr = encoding.encode_address(pk)
            if addr == avm_address:
                print(f"Pera Wallet Derivation Match found: m/44'/283'/{i}'/0/{j}")
                return kL, kR, pk
                
    raise ValueError("Mnemonic does not match AVM_ADDRESS across first 10 accounts/indexes")

async def run_e2e_test():
    pk_str = os.environ.get("X402_CLIENT_PRIVATE_KEY")
    mnemo = os.environ.get("X402_CLIENT_MNEMONIC")
    avm_address = os.environ.get("AVM_ADDRESS")
    signer = None
    
    if mnemo:
        # Normalize: replace commas/newlines with spaces
        mnemo = mnemo.replace(',', ' ').replace('\n', ' ').replace('\r', ' ')
        words = mnemo.strip().split()
        mnemo = ' '.join(words)
        
        if len(words) == 24:
            # Pera Universal Wallet (BIP39 Peikert Ed25519)
            if not avm_address:
                print("FAIL: AVM_ADDRESS must be set to find the correct 24-word account index.")
                sys.exit(1)
            try:
                kl, kr, pk = derive_pera_24_word(mnemo, avm_address)
                signer = TestnetSigner(kl=kl, kr=kr, pk=pk)
            except Exception as e:
                print(f"FAIL: Provided 24-word X402_CLIENT_MNEMONIC error: {e}")
                sys.exit(1)
        elif len(words) == 25:
            # Algorand Legacy Wallet
            try:
                pk_str = mnemonic.to_private_key(mnemo)
                signer = TestnetSigner(private_key=pk_str)
            except Exception as e:
                print(f"FAIL: Provided 25-word X402_CLIENT_MNEMONIC is invalid ({e}).")
                sys.exit(1)
        else:
            print(f"FAIL: Mnemonic has {len(words)} words. Expected 24 or 25.")
            sys.exit(1)
            
    if not signer:
        print("FAIL: No wallet credential found.")
        print("Please configure X402_CLIENT_MNEMONIC in your backend/.env file.")
        print("DO NOT commit the .env file.")
        sys.exit(1)
        
    if not encoding.is_valid_address(signer.address):
        print("FAIL: Derived address from private key is invalid.")
        sys.exit(1)
        
    if avm_address and signer.address != avm_address:
        print("FAIL: Wallet credential does not correspond to AVM_ADDRESS.")
        print("Please ensure AVM_ADDRESS matches the public address of your configured mnemonic.")
        sys.exit(1)
        
    print(f"--- Client Signer Initialized ---")
    print(f"Client Address: {signer.address}")
    
    from x402.http import x402HTTPClient
    import httpx
    
    # Initialize the client
    client = x402Client(x402ClientConfig(schemes=[]))
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
