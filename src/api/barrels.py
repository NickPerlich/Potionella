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
    # create transaction and ledger entries for each barrel purchased 
    if len(barrels_delivered) > 0:
        for barrel in barrels_delivered:
        # create transaction for each barrel
            description = f"Potionella bought {barrel.quantity} {barrel.sku} for {barrel.price*barrel.quantity} gold."
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) \
                                                             VALUES (:desc) \
                                                             RETURNING id"), {
                                                                 'desc': description
                                                             })
                transaction_id = result.scalar()
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("INSERT INTO ledger_entries (transaction_id, potion_type, item_type, change) \
                                                    VALUES \
                                                        (:trans_id, :p_type, :i_type1, :delta1) \
                                                        (:trans_id, NULL, :i_type2, :delta2)"), {
                                                        'trans_id': transaction_id,
                                                        'p_type': barrel.potion_type,
                                                        'i_type1': 'ml',
                                                        'delta1': barrel.quantity * barrel.ml_per_barrel,
                                                        'i_type2': 'gold',
                                                        'delta2': barrel.quantity * barrel.price
                                                    })
        
        

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    
    # from the database, get all barrels I want to buy sorted by priority
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT sku, wish \
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
            wish = row.wish
            while gold >= barrel_for_sale.price and wish > 0:
                quantity += 1
                wish -= 1
                gold -= barrel_for_sale.price 
            barrels_to_purchase.append({ 'sku': row.sku, 'quantity': quantity })

    return barrels_to_purchase


