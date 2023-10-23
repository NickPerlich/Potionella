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
        result = connection.execute(sqlalchemy.text("""SELECT 
                                           SUM(CASE
                                                WHEN item_type = 'potion' THEN change
                                                ELSE 0
                                           END)
                                           SUM(CASE
                                                WHEN item_type = 'ml' THEN change
                                                ELSE 0
                                           END)
                                           SUM(CASE
                                                WHEN item_type = 'gold' THEN change
                                                ELSE 0
                                           END)""")).all
    
    return {"number_of_potions": result[0], "ml_in_barrels": result[1], "gold": result[2]}

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
