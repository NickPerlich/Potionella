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

    if len(potions_delivered) > 0:
        # log all the potions I bottled and all the ml I spent
        for potion in potions_delivered:
            description = f"Potionella bottled {potion.quantity} {potion.potion_type} potions."
            with db.engine.begin() as connection:
                transaction_id = connection.execute(sqlalchemy.text("""INSERT INTO transactions (description) 
                                                             VALUES (:desc) 
                                                             RETURNING id"""), {
                                                                 'desc': description
                                                             }).scalar()
            params = []
            params.append({
                'trans_id': transaction_id,
                'color': potion.potion_type,
                'patron': None,
                'i_type': 'potion',
                'delta': potion.quantity
            })
            for i in range(len(potion.potion_type)):
                color = [0,0,0,0]
                if potion.potion_type[i] > 0:
                    color[i] = 1
                    params.append({
                        'trans_id': transaction_id,
                        'color': color,
                        'patron': None,
                        'i_type': 'ml',
                        'delta': -(potion.potion_type[i] * potion.quantity)
                    })
                
            # ml lost potions gained
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("""INSERT INTO ledger_entries 
                                                    (transaction_id, item_type, ml_type, customer, change) 
                                                    VALUES 
                                                        (:trans_id, :i_type, :color, :patron, :delta)"""), params)
            
        
        
        

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # from the database, get all potions I want to bottle sorted by priority
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""SELECT catalog.potion_type, bottler.wish 
                                                     FROM bottler 
                                                     JOIN catalog ON bottler.potion_id = catalog.id
                                                     WHERE bottler.bottle = TRUE 
                                                     ORDER BY bottler.priority ASC""")).all()
        
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("""SELECT change, ml_type
                                                            FROM ledger_entries
                                                            WHERE item_type = 'ml'""")).all()

    # set up array which represents how much ml I have   
    ml_owned = [0,0,0,0]

    for row in inventory:
        if row.ml_type == [1,0,0,0]:
            ml_owned[0] += row.change
        elif row.ml_type == [0,1,0,0]:
            ml_owned[1] += row.change
        elif row.ml_type == [0,0,1,0]:
            ml_owned[2] += row.change
        elif row.ml_type == [0,0,0,1]:
            ml_owned[3] += row.change
        
    # create the list of potions to bottle and stop when I can't afford any more
    potions_to_bottle = []

    for row in result:
        quantity = 0
        wish = row.wish
        while all(ml_possessed >= ml_required for ml_possessed, ml_required in zip(ml_owned, row.potion_type)) and wish > 0:
            quantity += 1
            wish -= 1
            ml_owned = [ml_possessed - ml_required for ml_possessed, ml_required in zip(ml_owned, row.potion_type)]
        if quantity > 0:
            potions_to_bottle.append({ 'potion_type': row.potion_type, 'quantity': quantity })

    return potions_to_bottle



