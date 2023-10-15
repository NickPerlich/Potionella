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
        result = connection.execute(sqlalchemy.text("SELECT bruh, name, quantity, price, potion_type \
                                                     FROM inventory \
                                                     WHERE for_sale = TRUE \
                                                     ORDER BY priority ASC")).all()

    potions_for_sale = []
    quantity = 0

    for row in result:
        if quantity == 20:
            break
        potions_for_sale.append({
            'sku': row.bruh,
            'name': row.name,
            'quantity': row.quantity,
            'price': row.price,
            'potion_type': row.potion_type
        })
        quantity += row.quantity

    return potions_for_sale