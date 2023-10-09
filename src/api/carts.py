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
    # get the current number of carts
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_carts FROM global_inventory")).first()
    # create a new cart in the carts table
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("INSERT INTO carts (RED_POTION_0, GREEN_POTION_0, BLUE_POTION_0) VALUES (0, 0, 0)"))
    # increment the number of carts in global_inventory
    params = {
            'num_carts': result.num_carts+1
        }
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_carts = :num_carts"), params)
    # return the id of the new cart
    return {"cart_id": result.num_carts + 1}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    if item_sku == "RED_POTION_0":
        params = {
            'cart_id': cart_id,
            'RED_POTION_0': cart_item
        }
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE carts SET RED_POTION_0 = :RED_POTION_0 WHERE cart_id = :cart_id"), params)
    elif item_sku == "GREEN_POTION_0":
        params = {
            'cart_id': cart_id,
            'GREEN_POTION_0': cart_item
        }
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE carts SET GREEN_POTION_0 = :GREEN_POTION_0 WHERE cart_id = :cart_id"), params)
    elif item_sku == "BLUE_POTION_0":
        params = {
            'cart_id': cart_id,
            'BLUE_POTION_0': cart_item
        }
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE carts SET BLUE_POTION_0 = :BLUEPOTION_0 WHERE cart_id = :cart_id"), params)
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, gold FROM global_inventory")).first()

    params = {
        'gold': result.gold + 50, 
        'num_red_potions': result.num_red_potions - 1,
    }

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :num_red_potions, gold = :gold"), params)

    return {"total_potions_bought": 1, "total_gold_paid": 50}
    

