# LedgerLight  

LedgerLight is a self-hosted personal finance & investment dashboard that merges portfolio analytics, budgeting, and transaction tracking into one unified platform. It is designed to run on a Raspberry Pi cluster with a lean footprint, storing all data locally without cloud dependencies.  

## Project Objectives  
- Combine portfolio, budgeting, and net-worth views into a single dashboard.  
- Store all data locally — no cloud dependencies.  
- Support multi-currency (CAD, USD, BRL) assets.  
- Allow easy CSV/OFX imports for banks and brokerages.  
- Run lean — optimized for Raspberry Pi hardware.  
- Be modular so other developers can fork and extend.  

## Core Features (MVP)  
- 📈 Investment tracking (stocks, ETFs, crypto, cash)  
- 💰 Budgeting with categories and goals  
- 🔄 Multi-currency FX conversions  
- 🧾 CSV/OFX import & reconciliation  
- 📤 Local backup to S3-compatible storage (MinIO/B2)  
- 🔒 Encrypted secrets (no external vault)  

## Repo Structure  
```
ledgerlight/  
 ├── backend/  
 │   ├── api/  
 │   ├── models/  
 │   └── ingest/  
 ├── frontend/  
 │   ├── components/  
 │   └── pages/  
 ├── k8s/  
 │   ├── deploy.yaml  
 │   ├── service.yaml  
 │   └── ingress.yaml  
 ├── .github/workflows/  
 │   └── deploy.yml  
 └── README.md  
```
