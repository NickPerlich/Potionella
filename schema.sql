BARRELS:
create table
  public.barrels (
    id integer generated by default as identity,
    sku text not null,
    priority integer null,
    name text null,
    potion
    type integer[] null,
    purchase boolean not null default false,
    wish integer not null default 0,
    constraint barrels_pkey primary key (id)
  ) tablespace pg_default;
BOTTLER:
create table
  public.bottler (
    id integer generated by default as identity,
    potion_id integer null,
    bottle boolean not null default false,
    priority integer null,
    wish integer null default 0,
    constraint bottler_pkey primary key (id),
    constraint bottler_potion_id_fkey foreign key (potion_id) references catalog (id)
  ) tablespace pg_default;
  CART_ITEMS:
create table
  public.cart_items (
    id integer generated by default as identity,
    cart_id integer null,
    sku text null,
    quantity integer not null default 0,
    catalog_id integer not null,
    constraint cart_items_pkey primary key (id),
    constraint cart_items_cart_id_fkey foreign key (cart_id) references carts (id),
    constraint cart_items_catalog_id_fkey foreign key (catalog_id) references catalog (id)
  ) tablespace pg_default;
  CARTS:
  create table
  public.carts (
    id integer generated by default as identity,
    customer text null,
    created_at timestamp with time zone not null default (now() at time zone 'pst'::text),
    constraint carts_pkey primary key (id)
  ) tablespace pg_default;
  CATALOG:
  create table
  public.catalog (
    id integer generated by default as identity,
    potion_type integer[] not null,
    price integer not null default 0,
    sku text null,
    name text null,
    for_sale boolean not null default false,
    priority integer not null default 0,
    constraint potions_pkey primary key (id)
  ) tablespace pg_default;
  LEDGER_ENTRIES:
  create table
  public.ledger_entries (
    id integer generated by default as identity,
    transaction_id integer not null default '-1'::integer,
    change integer not null default 0,
    ml_type integer[] null,
    item_type text null,
    cart_id integer null,
    customer text null,
    constraint ledger_entries_pkey primary key (id),
    constraint ledger_entries_cart_id_fkey foreign key (cart_id) references carts (id),
    constraint ledger_entries_transaction_id_fkey foreign key (transaction_id) references transactions (id)
  ) tablespace pg_default;
  TRANSACTIONS:
  create table
  public.transactions (
    id integer generated by default as identity,
    description text null,
    created_at timestamp with time zone not null default (now() at time zone 'pst'::text),
    constraint transactions_pkey primary key (id)
  ) tablespace pg_default;