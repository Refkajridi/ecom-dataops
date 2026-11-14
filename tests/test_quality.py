from datetime import date

from generate_orders import generate


def scalar(con, sql):
    return con.execute(sql).fetchone()[0]


def test_amount_positive(con):
    assert scalar(con, "select count(*) from raw.orders where amount <= 0") == 0


def test_quantity_positive(con):
    assert scalar(con, "select count(*) from raw.orders where quantity <= 0") == 0


def test_currency_valid(con):
    assert scalar(con, "select count(*) from raw.orders where currency not in ('EUR','USD')") == 0


def test_order_id_unique(con):
    assert scalar(con, "select count(*) - count(distinct order_id) from raw.orders") == 0


def test_product_ids_exist(con):
    sql = """select count(*) from raw.orders o
             left join raw.products p using (product_id)
             where p.product_id is null"""
    assert scalar(con, sql) == 0


def test_generation_is_deterministic():
    # base de l'idempotence : même jour => mêmes commandes
    a = generate(date(2026, 11, 1))
    b = generate(date(2026, 11, 1))
    assert a.equals(b)