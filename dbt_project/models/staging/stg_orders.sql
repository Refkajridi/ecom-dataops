select order_id, customer_id, product_id, quantity, amount, currency,
       created_at, cast(created_at as date) as order_date
from {{ source('raw', 'orders') }}
where amount > 0 and quantity > 0