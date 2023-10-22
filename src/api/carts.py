from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    # create a new cart in the carts table
    with db.engine.begin() as connection:
        cart_id = connection.execute(sqlalchemy.text("INSERT INTO carts (customer) \
                                                     VALUES (:patron) \
                                                     RETURNING id"), {
            'patron': new_cart.customer
        }).scalar()
    # return the id of the new cart
    return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""SELECT id 
                                                    FROM catalog 
                                                    WHERE sku = :item_sku"""), {
                                                        'item_sku': item_sku
                                                    }).first()

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("""INSERT INTO cart_items (cart_id, catalog_id, sku, quantity) 
                                            VALUES (:id, :cat_id, :item_sku, :quantity)"""), {
                                                'id': cart_id,
                                                'cat_id': result.id,
                                                'item_sku': item_sku,
                                                'quantity': cart_item.quantity
                                            })

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""SELECT catalog.price, catalog.potion_type, cart_items.quantity 
                                                     FROM cart_items 
                                                     JOIN catalog ON catalog.sku = cart_items.sku
                                                     WHERE cart_items.cart_id = :cart_id"""), {
                                                         'cart_id': cart_id
                                                     }).all()
    
    potions_bought = 0
    gold_paid = 0

    # subtract potions and add gold
    for row in result:
        potions_bought += row.quantity
        gold_paid += row.quantity * row.price
        description = f"Potionella sold {row.quantity} {row.potion_type} potions for {row.quantity * row.price} gold."
        with db.engine.begin() as connection:
            transaction_id = connection.execute(sqlalchemy.text("""INSERT INTO transactions (description) 
                                                            VALUES (:desc) 
                                                            RETURNING id"""), {
                                                                'desc': description
                                                            }).scalar()
        with db.enginge.begin() as connection:
            connection.execute(sqlalchemy.text("""INSERT INTO ledger_entries 
                                                    (transaction_id, item_type, ml_type, change) 
                                                    VALUES 
                                                        (:trans_id, :i_type, :color, :delta)"""), [{
                                                        'trans_id': transaction_id,
                                                        'color': row.potion_type,
                                                        'i_type': 'potion',
                                                        'delta': -(row.quantity)},
                                                        {
                                                            'trans_id': transaction_id,
                                                            'color': None,
                                                            'i_type': 'gold',
                                                            'delta': row.quantity * row.price
                                                        }])
        
    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_paid}
    

