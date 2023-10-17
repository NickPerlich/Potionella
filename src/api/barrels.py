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

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    gold_spent = 0
    # add all the ml I bought to inventory 
    if len(barrels_delivered) > 0:
        for barrel in barrels_delivered:
            gold_spent += barrel.price * barrel.quantity
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE inventory \
                                                    SET quantity = inventory.quantity + :ml_purchased \
                                                    WHERE potion_type = :type"), {
                                                        'ml_purchased': barrel.ml_per_barrel * barrel.quantity,
                                                        'type': barrel.potion_type
                                                    })
            print(barrel.ml_per_barrel * barrel.quantity)
            print(barrel.potion_type)
        # subtract gold I spent
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE inventory \
                                                SET quantity = inventory.quantity - :gold_spent \
                                                WHERE name = 'gold'"), {
                                                    'gold_spent': gold_spent
                                                })

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
        inventory_result = connection.execute(sqlalchemy.text("SELECT quantity \
                                                               FROM inventory \
                                                               WHERE name = 'gold'")).first()
        gold = inventory_result.quantity
    
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
            barrels_to_purchase.append({ 'sku': row.sku, 'quantity': quantity })

    print(barrels_to_purchase)

    return barrels_to_purchase


