select
    o.order_id, o.order_date, o.customer_id, o.product_id,
    p.category, o.quantity, o.currency, o.amount,
    case when o.currency = 'USD'
         then round(o.amount / fx.eur_usd, 2)
         else o.amount end as amount_eur,
    round(o.quantity * p.cost, 2) as cost_total
from {{ ref('stg_orders') }} o
join {{ ref('stg_products') }} p using (product_id)
left join {{ ref('stg_fx_rates') }} fx on fx.rate_date = o.order_date