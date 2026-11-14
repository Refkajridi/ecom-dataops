select product_id, name, category, price, cost
from {{ source('raw', 'products') }}