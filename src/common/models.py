from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SNssai(BaseModel):
    sst: int
    sd: str


class CreateSessionRequest(BaseModel):
    supi: str
    gpsi: str
    pduSessionId: int
    dnn: str
    sNssai: SNssai
    servingNfId: str
    anType: str


class PDUSession(BaseModel):
    id: Optional[str] = None
    supi: str
    pduSessionId: int
    dnn: str
    ipAddress: str
    status: str
    createdAt: datetime = datetime.now()


class N1N2MessageTransfer(BaseModel):
    pduSessionId: int
    sNssai: SNssai
    dnn: str


class PFCPSessionEstablishmentRequest(BaseModel):
    supi: str
    pduSessionId: int
    dnn: str


class PFCPSessionEstablishmentResponse(BaseModel):
    seid: int
    ipAddress: str
    status: str
