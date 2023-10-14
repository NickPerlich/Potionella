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
    
    # from the database, get all barrels I want to buy sorted by priority
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT sku, quantity \
                                                     FROM barrels \
                                                     WHERE purchase = TRUE \
                                                     ORDER BY priority ASC")).all()
        
    with db.engine.begin() as connection:
        inventory_result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()
        gold = inventory_result.gold
    
    # create the list of barrels to purchase and make sure all the barrels I want to buy are for sale and stop when I can't afford any more
    barrels_to_purchase = []
    for row in result:
        barrel_for_sale = next((barrel for barrel in wholesale_catalog if barrel.sku == row.sku), None)
        if barrel_for_sale is not None and gold >= barrel_for_sale.price:
            quantity = 0
            wish = row.quantity
            while gold >= barrel_for_sale.price and wish > 0:
                quantity += 1
                wish -= 1
                gold -= barrel_for_sale.price 
            barrels_to_purchase.append({ "sku": row.sku, "quantity": quantity })

    return barrels_to_purchase


