from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.schemas import AddCustomerRequest, AddCustomerResponse

router = APIRouter(tags=["Customers"])


@router.post("/add_customer", response_model=AddCustomerResponse)
def add_customer(
    payload: AddCustomerRequest,
    db: Session = Depends(get_db),
):
    """
    Create a new customer.
    If the phone number already exists, return the existing customer_id.
    """
    customer_id = crud.add_customer(
        db=db,
        name=payload.name.strip(),
        phone=payload.phone.strip(),
    )
    return AddCustomerResponse(customer_id=str(customer_id))
