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

    for potion in potions_delivered:
        if potion.potion_type == [100, 0, 0, 0]:
            small_red_potion = potion

    if small_red_potion is not None:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_red_potions FROM global_inventory")).first()
        
        # subtract red ml and add red potions to Potionella's storage
        params = {
            'num_red_potions': result.num_red_potions + small_red_potion.quantity,
            'num_red_ml': result.num_red_ml - small_red_potion.quantity*100,
        }

        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :num_red_potions, num_red_ml = :num_red_ml"), params)

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    # find out how much red ml potionella has
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_red_potions FROM global_inventory")).first()
    
    # if potionella has at least 100 red ml plan to bottle into potions
    if result.num_red_ml >= 100:
        return [
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": result.num_red_ml//100,
                }
            ]
    else :
        return []


