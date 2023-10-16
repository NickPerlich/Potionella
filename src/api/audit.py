from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT quantity \
                                                     FROM catalog")).all()
        
    num_potions = 0
    for row in result:
        num_potions += row.quantity

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT quantity \
                                                     FROM inventory \
                                                     ORDER BY id ASC")).all()
        
    num_ml = 0
    for row in result[1:]:
        num_ml += row.quantity

    num_gold = result[0].quantity
    
    return {"number_of_potions": num_potions, "ml_in_barrels": num_ml, "gold": num_gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
