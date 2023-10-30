from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """
    
    meta = sqlalchemy.MetaData()
    meta.reflect(bind=db.engine)
    max_results = 5
    limit = max_results + 1
    if search_page != "":
        offset = int(search_page) * max_results
    else:
        offset = 0
    # get a table from metadata => print(meta.tables['ledger_entries'])

    ledger_entries, cart_items, transactions = (meta.tables['ledger_entries'], meta.tables['cart_items'], meta.tables['transactions'])

    if sort_col == "customer_name" and sort_order == "asc":
        order_by = ledger_entries.c.customer
    elif sort_col == "customer_name" and sort_order == "desc":
        order_by = sqlalchemy.desc(ledger_entries.c.customer)
    elif sort_col == "item_sku" and sort_order == "asc":
        order_by = cart_items.c.sku
    elif sort_col == "item_sku" and sort_order == "desc":
        order_by = sqlalchemy.desc(cart_items.c.sku)
    elif sort_col == "line_item_total" and sort_order == "asc":
        order_by = ledger_entries.c.change
    elif sort_col == "line_item_total" and sort_order == "desc":
        order_by = sqlalchemy.desc(ledger_entries.c.change)
    elif sort_col == "timestamp" and sort_order == "asc":
        order_by = transactions.c.created_at
    elif sort_col == "timestamp" and sort_order == "desc":
        order_by = sqlalchemy.desc(transactions.c.created_at)
    

    stmt = (
        sqlalchemy.select(
            ledger_entries.c.id,
            cart_items.c.sku,
            ledger_entries.c.customer,
            ledger_entries.c.change,
            transactions.c.created_at
        )
        .select_from(
            ledger_entries
            .join(transactions, ledger_entries.c.transaction_id == transactions.c.id)
            .join(cart_items, ledger_entries.c.cart_id == cart_items.c.cart_id)
        )
        .where(ledger_entries.c.item_type == 'gold')
        .limit(limit)
        .offset(offset)
        .order_by(order_by, ledger_entries.c.id)
    )

    if customer_name != "":
        stmt = stmt.where(ledger_entries.c.customer.ilike(f"%{customer_name}%"))

    if potion_sku != "":
        stmt = stmt.where(cart_items.c.sku.ilike(f"%{potion_sku}%"))

    with db.engine.begin() as connection:
        result = connection.execute(stmt)

    search_results = []
    len_result = 0

    for row in result:
        len_result += 1
        if len_result == limit:
            break
        search_results.append(
            {
                "line_item_id": row.id,
                "item_sku": row.sku,
                "customer_name": row.customer,
                "line_item_total": row.change,
                "timestamp": row.created_at
            }
        )

    previous = ""
    next_page = ""
    if search_page != "":
        previous = str(int(search_page)-1)
        if len_result > max_results:
            next_page = str(int(search_page)+1)
    else:
        if len_result > max_results:
            next_page = '1'

    if search_page == "0":
        previous = ""

    return {
        "previous": previous,
        "next": next,
        "results": search_results,
    }


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

        meta = sqlalchemy.MetaData()
        meta.reflect(bind=db.engine)
        carts = meta.tables['carts']
        customer = connection.execute(sqlalchemy.select(carts.c.customer).where(carts.c.id == cart_id)).first().customer

        # subtract potions and add gold
        for row in result:
            potions_bought += row.quantity
            gold_paid += row.quantity * row.price
            description = f"Potionella sold {row.quantity} {row.potion_type} potions for {row.quantity * row.price} gold to {customer}."
            transaction_id = connection.execute(sqlalchemy.text("""INSERT INTO transactions (description) 
                                                                VALUES (:desc) 
                                                                RETURNING id"""), {
                                                                    'desc': description
                                                                }).scalar()
            
            connection.execute(sqlalchemy.text("""INSERT INTO ledger_entries 
                                                        (transaction_id, item_type, ml_type, cart_id, customer, change) 
                                                        VALUES 
                                                            (:trans_id, :i_type, :color, :c_id, :patron, :delta)"""), [{
                                                            'trans_id': transaction_id,
                                                            'color': row.potion_type,
                                                            'c_id': cart_id,
                                                            'patron': customer, 
                                                            'i_type': 'potion',
                                                            'delta': -(row.quantity)},
                                                            {
                                                                'trans_id': transaction_id,
                                                                'color': None,
                                                                'c_id': cart_id,
                                                                'patron': customer, 
                                                                'i_type': 'gold',
                                                                'delta': row.quantity * row.price
                                                            }])
        
    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_paid}
    

