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
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions FROM global_inventory")).first()

    small_red_potion = {
                        "sku": "RED_POTION_0",
                        "name": "red potion",
                        "quantity": 1,
                        "price": 50,
                        "potion_type": [100, 0, 0, 0], 
    }
    small_green_potion = {
                        "sku": "GREEN_POTION_0",
                        "name": "green potion",
                        "quantity": 1,
                        "price": 50,
                        "potion_type": [0, 100, 0, 0],
    }
    small_blue_potion = {
                        "sku": "BLUE_POTION_0",
                        "name": "blue potion",
                        "quantity": 1,
                        "price": 50,
                        "potion_type": [0, 0, 100, 0],
    }

    potions_for_sale = []

    if result.num_red_potions >= 1 :
        potions_for_sale.append(small_red_potion)
    if result.num_green_potions >= 1 :
        potions_for_sale.append(small_green_potion)
    if result.num_blue_potions >= 1 :
        potions_for_sale.append(small_blue_potion)

    return potions_for_sale