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
    return {"cart_id": 1}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    with db.engine.begin() as connection:
        num_red_potions = connection.execute("SELECT num_red_potions FROM global_inventory")

    with db.engine.begin() as connection:
        gold = connection.execute("SELECT gold FROM global_inventory")
        
    if num_red_potions >= 1 :
        params = {'gold': gold + 50, 'num_red_potions': num_red_potions + 1}

        with db.engine.begin() as connection:
            connection.execute("UPDATE global_inventory SET num_red_potions = :num_red_potions, gold = :gold", **params)
        return {"total_potions_bought": 1, "total_gold_paid": 50}
    else :
        return {"total_potions_bought": 0, "total_gold_paid": 0}


