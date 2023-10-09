from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from optimization import knapSack

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

    #check if anything was purchased
    rbarrel = None
    gbarrel = None
    bbarrel = None

    for barrel in barrels_delivered:
        if barrel.sku == "SMALL_RED_BARREL":
            rbarrel = barrel
        if barrel.sku == "SMALL_GREEN_BARREL":
            gbarrel = barrel
        if barrel.sku == "SMALL_BLUE_BARREL":
            bbarrel = barrel
            
    #update database if small red barrel was purchased
    if rbarrel is not None:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT gold, num_red_ml FROM global_inventory")).first()

        # subtract cost of one small red barrel from Potionella's gold funds and add one small red barrel's worth of red ml to Potionella's red ml amount 
        params = {
            'gold': result.gold - rbarrel.price,
            'num_red_ml': result.num_red_ml + rbarrel.ml_per_barrel,
        }
        
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :gold, num_red_ml = :num_red_ml"), params)
    #update database if small green barrel was purchased
    if gbarrel is not None:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT gold, num_green_ml FROM global_inventory")).first()

        # subtract cost of one small green barrel from Potionella's gold funds and add one small green barrel's worth of green ml to Potionella's green ml amount 
        params = {
            'gold': result.gold - gbarrel.price,
            'num_green_ml': result.num_green_ml + gbarrel.ml_per_barrel,
        }
        
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :gold, num_green_ml = :num_green_ml"), params)
    #update database if small blue barrel was purchased
    if bbarrel is not None:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT gold, num_blue_ml FROM global_inventory")).first()

        # subtract cost of one small blue barrel from Potionella's gold funds and add one small blue barrel's worth of blue ml to Potionella's blue ml amount 
        params = {
            'gold': result.gold - bbarrel.price,
            'num_blue_ml': result.num_blue_ml + bbarrel.ml_per_barrel,
        }
        
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :gold, num_blue_ml = :num_blue_ml"), params)

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    # get how many red potions and gold Potionella has in inventory
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_blue_potions, num_green_potions, gold FROM global_inventory")).first()
    
    # check what is for sale
    rbarrel = None
    gbarrel = None
    bbarrel = None

    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_RED_BARREL":
            rbarrel = barrel
        if barrel.sku == "SMALL_GREEN_BARREL":
            gbarrel = barrel
        if barrel.sku == "SMALL_BLUE_BARREL":
            bbarrel = barrel

    prices = []
    demands = []

    #buy barrels as needed
    if rbarrel is not None and result.num_red_potions < 10 and rbarrel.quantity >= 1:
        prices.append(rbarrel.price)
        demands.append(result.num_red_potions)
    if gbarrel is not None and result.num_green_potions < 10 and gbarrel.quantity >= 1:
        prices.append(gbarrel.price)
        demands.append(result.num_green_potions)
    if bbarrel is not None and result.num_blue_potions < 10 and bbarrel.quantity >= 1:
        prices.append(bbarrel.price)   
        demands.append(result.num_blue_potions)
        
    # the demand of a potion type is greater the less of it I have and the order is [r,g,b,d]
    demands.sort(reverse=True)
        
    _, items_taken = knapSack(result.gold, len(prices), prices, demands)

    small_red_barrel = { "sku": "SMALL_RED_BARREL", "quantity": 1}
    small_green_barrel = { "sku": "SMALL_GREEN_BARREL", "quantity": 1}
    small_blue_barrel = { "sku": "SMALL_BLUE_BARREL", "quantity": 1}

    barrels = [small_red_barrel, small_green_barrel, small_blue_barrel]

    barrels_to_purchase = barrels[:len(items_taken)]
    
    if len(items_taken) > 0:
        return barrels_to_purchase
    else :
        return []


