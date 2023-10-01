from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    #make sure there is a small red barrel for sale
    small_red_barrel = None

    for barrel in barrels_delivered:
        if barrel.sku == "SMALL_RED_BARREL":
            small_red_barrel = barrel

    if small_red_barrel is not None:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT gold, num_red_ml FROM global_inventory")).first()

        # subtract cost of one small red barrel from Potionella's gold funds and add one small red barrel's worth of red ml to Potionella's red ml amount 
        params = {
            'gold': result.gold - small_red_barrel.price,
            'num_red_ml': result.num_red_ml + small_red_barrel.ml_per_barrel,
        }
        
        with db.engine.bein() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :gold, num_red_ml :num_red_ml"), **params)

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    # get how many red potions and gold Potionella has in inventory
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, gold FROM global_inventory")).first()

    num_red_potions_in_inventory = result.num_red_potions
    gold = result.gold
    
    # check if there is a small red barrel for sale
    small_red_barrel = None

    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_RED_BARREL":
            small_red_barrel = barrel
    # if Potionella has less than ten red potions in stock, there is a small red barrel for sale and Potionella has enough funds
    if num_red_potions_in_inventory < 10 and small_red_barrel.quantity >= 1 and gold >= small_red_barrel.price and small_red_barrel is not None:
        return [
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
            }
        ]
    else :
        return []


