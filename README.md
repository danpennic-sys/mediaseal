# MediaSeal

**Local-first media evidence hasher and QuantumGuard sealer for field operators.**

Offline. Deterministic. Pay once. Compatible with QuantumGuard CONTRACT-v1, FieldSeal, JobSeal, VeriQuote, CloseSeal, LifecycleSeal, and Evidence-Core.

## Why MediaSeal?

Field operators need tamper-evident proof of site conditions, completed work, materials, and damage. Photos and videos on phones are easy to dispute ("that wasn't taken today", "the file was edited").

MediaSeal walks a folder (or list) of media files, computes deterministic SHA-256 hashes, records filenames + sizes + optional basic metadata, and seals the entire set into a client-verifiable QuantumGuard evidence bundle.

- No SaaS. No subscription. Runs completely offline after key setup.
- Clients (or their auditors) verify the pack with the free QuantumGuard verifier (`qg verify`).
- Media files themselves stay local; only the cryptographic hashes + metadata go into the sealed pack.
- Pairs with FieldSeal / JobSeal for full job context and with Chaser for invoicing.

## Quick Start

```bash
# Optional but recommended for real Ed25519 signatures
pip install cryptography

python3 src/mediaseal.py --demo
python3 src/mediaseal.py --dir ./site-photos --job-id JOB-2026-042 --out sealed_media.json
```

Verify the output with the QuantumGuard CLI (from the quantumguard repo):

```bash
qg verify sealed_media.json
```

Expected verdict: PASS (when using real cryptography).

## What you can sell

| SKU       | Price | Includes                                      |
|-----------|-------|-----------------------------------------------|
| Operator  | $69   | CLI + key setup guide + 1-year email support |
| Command   | $189  | + batch/recursive mode + HTML report + reseller rights for client packs |
| Agency    | $479  | + white-label HTML + design partner onboarding |

Purchase / access: danpennic@gmail.com

Source remains free under Apache-2.0 OR MIT. Commercial Operator Pack sold separately.

## Stack Fit

- Python CLI (same family as VeriQuote, FieldSeal, JobSeal, CloseSeal, LifecycleSeal)
- Emits QuantumGuard CONTRACT-v1 bundles (Ed25519, deterministic hashing)
- Local key storage (PEM)
- Pure standard library + optional cryptography — no heavy deps

## License

Apache-2.0 OR MIT
