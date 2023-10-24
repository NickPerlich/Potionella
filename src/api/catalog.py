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
        result = connection.execute(sqlalchemy.text("""SELECT sku, name, price, potion_type 
                                                     FROM catalog 
                                                     WHERE for_sale = TRUE 
                                                     ORDER BY priority ASC""")).all()

    potions_for_sale = []
    quantity = 0

    with db.engine.begin() as connection:
        for row in result:
            if quantity == 20:
                break
            amount = connection.execute(sqlalchemy.text("""SELECT SUM(change)
                                                        FROM ledger_entries
                                                        WHERE ml_type = :type"""),{
                                                            'type': row.potion_type
                                                        }).scalar()
            if amount is None or amount < 1:
                continue
            potions_for_sale.append({
                'sku': row.sku,
                'name': row.name,
                'quantity': amount,
                'price': row.price,
                'potion_type': row.potion_type
            })
            quantity += amount

    print(potions_for_sale)

    return potions_for_sale