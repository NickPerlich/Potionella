from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.
    with db.engine.begin() as connection:
        num_red_potions = connection.execute("SELECT num_red_potions FROM global_inventory")

    if num_red_potions >= 1 :
        return [
                {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": 1,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
            ]
    else :
        return [
            {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": 0,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
        ]