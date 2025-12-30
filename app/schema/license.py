from datetime import datetime as dt
from typing import Any
from typing import List
from typing import Optional

from pydantic import BaseModel


class Customer(BaseModel):
    id: int
    name: str
    email: str
    companyName: str
    created: dt


class LicenseResponse(BaseModel):
    productId: int
    id: int
    key: str
    created: dt
    expires: dt
    period: int
    f1: bool
    f2: bool
    f3: bool
    f4: bool
    f5: bool
    f6: bool
    f7: bool
    f8: bool
    notes: str
    block: bool
    globalId: int
    customer: Customer
    activatedMachines: List
    trialActivation: bool
    maxNoOfMachines: int
    allowedMachines: Optional[Any]
    dataObjects: List
    signDate: dt
    reseller: Optional[Any] = None
