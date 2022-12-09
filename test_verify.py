albedo_output = {
  "intent": "sign_message",
  "message": "e25f76e76ab7f7cca580",
  "pubkey": "GDLOOTWZR6FDC5A4LWWJH7ZJLM7AKOXGANU7CMVFLSTJYHOJLVOZLFTC",
  "signed_message": "GDLOOTWZR6FDC5A4LWWJH7ZJLM7AKOXGANU7CMVFLSTJYHOJLVOZLFTC:e25f76e76ab7f7cca580",
  "message_signature": "d7e32b4e9ac4ba1f95f3e4a33efd5c2a9344d89d9d48a19e53ab3e183cdf00684fa281ffb1b014764ded17b7db76f72e94aa576b131130ecf3d61da35d82b90f"
}

from stellar_sdk import Keypair
import hashlib

def verify_authorization(instance_id,source_account,authorization):
  keypair = Keypair.from_public_key(source_account)
  signed_message = (source_account + ":" + instance_id)
  hashed_message = hashlib.sha256(signed_message.encode('utf-8')).digest()
  keypair.verify(hashed_message,bytes.fromhex(authorization))

verify_authorization("e25f76e76ab7f7cca580","GDLOOTWZR6FDC5A4LWWJH7ZJLM7AKOXGANU7CMVFLSTJYHOJLVOZLFTC","d7e32b4e9ac4ba1f95f3e4a33efd5c2a9344d89d9d48a19e53ab3e183cdf00684fa281ffb1b014764ded17b7db76f72e94aa576b131130ecf3d61da35d82b90f")