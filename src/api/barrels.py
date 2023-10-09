from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from typing import List

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

# this function is an implementation of the solution to the 01-knapsack problem
# it returns table which is a 2d array where row is num_items and column is capacity
# it also returns items_taken which is a list of indices representing which (weight, value) items were taken
def knapSack(capacity: int, num_items: int, weights: List[int], values: List[float]):
    table = [[0] * (capacity+1) for _ in range(num_items+1)]
    # fill in the table using dynamic programming
    for n in range(1, num_items+1):
        for cap in range(1, capacity+1):
            item_weight = weights[n-1]
            item_value = values[n-1]
            if item_weight > cap:
                table[n][cap] = table[n-1][cap]
            else:
                table[n][cap] = max(table[n-1][cap-item_weight]+item_value, table[n-1][cap]) 

    #trace back through the table
    items_taken = []
    i = num_items
    j = capacity

    while i > 0 and j > 0:
        weight = weights[i-1]
        value = values[i-1]

        if weight > j or table[i][j] != table[i-1][j-weight]+value:
            i -= 1
        else:
            items_taken.append(i-1)
            i -= 1
            j -= weight

    return table, items_taken[::-1]

def invert_number(number):
    if number == 0:
        return 1000
    return 1 / number

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

    # prices is a list of barrel costs, num_potions is a list of how many potions of that color I have, and barrels is a list of the type of barrel
    prices = []
    num_potions = []
    barrels = []
    # all possible barrels that could be bought
    small_red_barrel = { "sku": "SMALL_RED_BARREL", "quantity": 1}
    small_green_barrel = { "sku": "SMALL_GREEN_BARREL", "quantity": 1}
    small_blue_barrel = { "sku": "SMALL_BLUE_BARREL", "quantity": 1}

    #decide which barrels to buy out of what is available
    if rbarrel is not None and result.num_red_potions < 10 and rbarrel.quantity >= 1:
        prices.append(rbarrel.price)
        num_potions.append(result.num_red_potions)
        barrels.append(small_red_barrel)
    if gbarrel is not None and result.num_green_potions < 10 and gbarrel.quantity >= 1:
        prices.append(gbarrel.price)
        num_potions.append(result.num_green_potions)
        barrels.append(small_green_barrel)
    if bbarrel is not None and result.num_blue_potions < 10 and bbarrel.quantity >= 1:
        prices.append(bbarrel.price)   
        num_potions.append(result.num_blue_potions)
        barrels.append(small_blue_barrel)
        
    # the demand of a potion type is greater the less of it I have
    demand = []
    for potion_amount in num_potions:
        demand.append(invert_number(potion_amount))
        
    # items_taken is a list of which barrels to buy
    _, items_taken = knapSack(result.gold, len(prices), prices, demand)

    # format the api response
    barrels_to_purchase = []

    for item in items_taken:
        barrels_to_purchase.append(barrels[item])
    # send the api response
    if len(items_taken) > 0:
        return barrels_to_purchase
    else :
        return []


