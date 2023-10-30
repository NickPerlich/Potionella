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
        result = connection.execute(sqlalchemy.text("""SELECT item_type, SUM(change) total 
                                                    FROM ledger_entries
                                                    GROUP BY item_type""")).all()

    for row in result:
        if row.item_type == 'potion':
            num_potions = row.total
        elif row.item_type == 'ml':
            num_ml = row.total
        elif row.item_type == 'gold':
            num_gold = row.total
    
    return {"number_of_potions": 0, "ml_in_barrels": num_ml, "gold": num_gold}

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
