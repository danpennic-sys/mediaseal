#!/usr/bin/env python3
"""
MediaSeal — local-first media evidence hasher and QuantumGuard sealer.
Compatible with QuantumGuard CONTRACT-v1 and the Operator Pages suite.
Offline after key setup. Deterministic payload hashing.
"""
import argparse
import json
import hashlib
import base64
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("Note: cryptography not installed. Using stub signatures. pip install cryptography for real Ed25519.")

MEDIA_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".mp4", ".mov", ".avi", ".mkv", ".pdf"}

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def load_or_create_key(key_path: Path):
    """Returns (private_key_or_None, public_key_hex)"""
    if not CRYPTO_AVAILABLE:
        return None, "00" * 32
    if key_path.exists():
        with open(key_path, "rb") as f:
            priv = serialization.load_pem_private_key(f.read(), password=None)
        pub = priv.public_key()
        pub_bytes = pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        return priv, pub_bytes.hex()
    else:
        priv = Ed25519PrivateKey.generate()
        pub = priv.public_key()
        pub_bytes = pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        pem = priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        key_path.write_bytes(pem)
        return priv, pub_bytes.hex()

def sign_payload(priv, payload_hash_hex: str) -> str:
    if not CRYPTO_AVAILABLE or priv is None:
        return "00" * 64
    hash_bytes = bytes.fromhex(payload_hash_hex)
    sig = priv.sign(hash_bytes)
    return sig.hex()

def collect_media(dir_path: Path, recursive: bool = False) -> list:
    media = []
    if not dir_path.exists():
        return media
    paths = dir_path.rglob("*") if recursive else dir_path.glob("*")
    for p in sorted(paths):
        if p.is_file() and p.suffix.lower() in MEDIA_EXTS:
            try:
                file_hash = hash_file(p)
                media.append({
                    "name": p.name,
                    "relative_path": str(p.relative_to(dir_path)),
                    "size_bytes": p.stat().st_size,
                    "sha256": file_hash,
                    "mtime_iso": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
                })
            except Exception as e:
                media.append({"name": p.name, "error": str(e)})
    return media

def build_evidence_pack(job_id: str, media_list: list, notes: str, priv, pub_hex: str, operator: str = "field-tech") -> dict:
    payload_obj = {
        "version": "1",
        "type": "media_evidence",
        "job_id": job_id,
        "notes": notes or "",
        "operator": operator,
        "media_count": len(media_list),
        "media": media_list,
        "sealed_at": datetime.now(timezone.utc).isoformat()
    }
    payload_bytes = json.dumps(payload_obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.b64encode(payload_bytes).decode("ascii")
    payload_hash = sha256_hex(payload_bytes)
    signature = sign_payload(priv, payload_hash)

    pack = {
        "version": "1",
        "payload": payload_b64,
        "payload_hash": payload_hash,
        "signature": signature,
        "public_key": pub_hex,
        "alg": "ed25519"
    }
    return pack

def demo():
    # Simulate a couple of media entries without real files
    media = [
        {
            "name": "before-unit.jpg",
            "relative_path": "before-unit.jpg",
            "size_bytes": 1843200,
            "sha256": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
            "mtime_iso": "2026-10-29T14:30:00+00:00"
        },
        {
            "name": "after-repair.mp4",
            "relative_path": "after-repair.mp4",
            "size_bytes": 15728640,
            "sha256": "fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321",
            "mtime_iso": "2026-10-29T15:45:00+00:00"
        }
    ]
    key_path = Path.home() / ".mediaseal_key.pem"
    priv, pub_hex = load_or_create_key(key_path)
    pack = build_evidence_pack("JOB-2026-DEMO", media, "Demo: capacitor replacement site photos.", priv, pub_hex)
    print(json.dumps(pack, indent=2))
    print("\n# Verify with: qg verify <this.json>  (from QuantumGuard)")

def main():
    parser = argparse.ArgumentParser(description="MediaSeal — local media evidence sealer")
    parser.add_argument("--demo", action="store_true", help="Run demo and print sealed pack")
    parser.add_argument("--dir", type=str, help="Directory containing media files")
    parser.add_argument("--job-id", type=str, default="unknown", help="Job identifier")
    parser.add_argument("--notes", type=str, default="", help="Optional notes")
    parser.add_argument("--operator", type=str, default="field-tech", help="Operator name")
    parser.add_argument("--out", type=str, help="Output sealed pack path")
    parser.add_argument("--key", type=str, default=str(Path.home() / ".mediaseal_key.pem"), help="Private key path")
    parser.add_argument("--recursive", action="store_true", help="Recurse into subdirectories")
    args = parser.parse_args()

    if args.demo:
        demo()
        return

    if not args.dir:
        parser.print_help()
        return

    dir_path = Path(args.dir)
    media_list = collect_media(dir_path, args.recursive)
    if not media_list:
        print(f"No media files found in {dir_path}")
        return

    key_path = Path(args.key)
    priv, pub_hex = load_or_create_key(key_path)
    pack = build_evidence_pack(args.job_id, media_list, args.notes, priv, pub_hex, args.operator)

    out_path = args.out or f"sealed_media_{args.job_id}.json"
    with open(out_path, "w") as f:
        json.dump(pack, f, indent=2)
    print(f"Sealed {len(media_list)} media files into {out_path}")
    print(f"Payload hash: {pack['payload_hash']}")
    print("Verify with QuantumGuard: qg verify", out_path)

if __name__ == "__main__":
    main()
