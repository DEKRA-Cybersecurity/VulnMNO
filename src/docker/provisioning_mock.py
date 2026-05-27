"""Minimal HTTP stub used by the docker-compose stack to simulate the
external provisioning system. Returns success for every activation request.

Run inside the provisioning-mock container:
    uvicorn provisioning_mock:app --host 0.0.0.0 --port 9000
"""
from __future__ import annotations

import secrets

from fastapi import FastAPI

app = FastAPI(title="VulnMNO provisioning mock")


@app.post("/activate")
def activate(payload: dict) -> dict:
    return {
        "provisioningId": "prov_" + secrets.token_hex(6),
        "status": "active",
    }


@app.post("/deactivate")
def deactivate(payload: dict) -> dict:
    return {"status": "deactivated"}
