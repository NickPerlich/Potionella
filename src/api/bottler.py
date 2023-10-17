from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)

    ml_spent = [0,0,0,0]

    if len(potions_delivered) > 0:
        # add all the potions I bottled to catalog 
        for potion in potions_delivered:
            ml_spent = [ml_lost + (ml_cost * potion.quantity) for ml_lost, ml_cost in zip(ml_spent, potion.potion_type)]
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE catalog \
                                                    SET quantity = catalog.quantity + :amount \
                                                    WHERE potion_type = :type"), {
                                                        'amount': potion.quantity,
                                                        'type': potion.potion_type
                                                    })
        # subtract ml I spent
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE inventory \
                                                SET quantity = CASE \
                                                    WHEN name = 'red_ml' THEN inventory.quantity - :red \
                                                    WHEN name = 'green_ml' THEN inventory.quantity - :green \
                                                    WHEN name = 'blue_ml' THEN inventory.quantity - :blue \
                                                    WHEN name = 'dark_ml' THEN inventory.quantity - :dark \
                                                    ELSE quantity \
                                                END"), {
                                                    'red': ml_spent[0],
                                                    'green': ml_spent[1],
                                                    'blue': ml_spent[2],
                                                    'dark': ml_spent[3]
                                                })
        

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # from the database, get all potions I want to bottle sorted by priority
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT catalog.potion_type, bottler.quantity \
                                                     FROM bottler \
                                                     JOIN catalog ON bottler.potion_id = catalog.id\
                                                     WHERE bottler.bottle = TRUE \
                                                     ORDER BY bottler.priority ASC")).all()
    print(result)
        
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT quantity \
                                                     FROM inventory \
                                                     ORDER BY id ASC")).all()
    print(inventory)

    # set up array which represents how much ml I have   
    ml_owned = []

    for row in inventory:
        ml_owned.append(row.quantity)

    # get rid of gold
    ml_owned.pop(0)
        
    # create the list of potions to bottle and stop when I can't afford any more
    potions_to_bottle = []

    for row in result:
        quantity = 0
        wish = row.quantity
        while all(ml_possessed >= ml_required for ml_possessed, ml_required in zip(ml_owned, row.potion_type)) and wish > 0:
            quantity += 1
            wish -= 1
            ml_owned = [ml_possessed - ml_required for ml_possessed, ml_required in zip(ml_owned, row.potion_type)]
        potions_to_bottle.append({ 'potion_type': row.potion_type, 'quantity': quantity })

    return potions_to_bottle



