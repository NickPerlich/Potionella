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

    small_red_potion = None
    small_green_potion = None
    small_blue_potion = None

    for potion in potions_delivered:
        if potion.potion_type == [100, 0, 0, 0]:
            small_red_potion = potion
        if potion.potion_type == [0, 100, 0, 0]:
            small_green_potion = potion
        if potion.potion_type == [0, 0, 100, 0]:
            small_blue_potion = potion

    if small_red_potion is not None:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_red_potions FROM global_inventory")).first()
        
        # subtract red ml and add red potions to Potionella's storage
        params = {
            'num_red_potions': result.num_red_potions + small_red_potion.quantity,
            'num_red_ml': result.num_red_ml - small_red_potion.quantity*100,
        }

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :num_red_potions, num_red_ml = :num_red_ml"), params)

    if small_green_potion is not None:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_green_potions FROM global_inventory")).first()
        
        # subtract green ml and add green potions to Potionella's storage
        params = {
            'num_green_potions': result.num_green_potions + small_green_potion.quantity,
            'num_green_ml': result.num_green_ml - small_green_potion.quantity*100,
        }

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = :num_green_potions, num_green_ml = :num_green_ml"), params)

    if small_blue_potion is not None:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT num_blue_ml, num_blue_potions FROM global_inventory")).first()
        
        # subtract blue ml and add blue potions to Potionella's storage
        params = {
            'num_blue_potions': result.num_blue_potions + small_blue_potion.quantity,
            'num_blue_ml': result.num_blue_ml - small_blue_potion.quantity*100,
        }

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = :num_blue_potions, num_blue_ml = :num_blue_ml"), params)

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
        
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT quantity \
                                                     FROM inventory \
                                                     ORDER BY id ASC")).all()

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



