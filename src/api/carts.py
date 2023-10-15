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
        result = connection.execute(sqlalchemy.text("INSERT INTO carts (customer) \
                                                     VALUES (:patron) \
                                                     RETURNING cart_id"), {
            'patron': new_cart.customer
        })
        cart_id = result.scalar()
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
        result = connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, sku, quantity) \
                                                     VALUES (:id, :item_sku, :quantity)"), {
                                                         'id': cart_id,
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
        result = connection.execute(sqlalchemy.text("UPDATE catalog \
                                                     SET quantity = catalog.quantity - cart_items.quantity \
                                                     FROM cart_items \
                                                     WHERE catalog.sku = cart_items.sku and cart_items.cart_id = :cart_id;"), {
                                                         'cart_id': cart_id
                                                     })

    return {"total_potions_bought": , "total_gold_paid": }
    

