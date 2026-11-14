with bounds as (
    select
        least(
            (select min(rate_date) from {{ source('raw', 'fx_rates') }}),
            (select min(cast(created_at as date)) from {{ source('raw', 'orders') }})
        ) as d0,
        greatest(
            (select max(rate_date) from {{ source('raw', 'fx_rates') }}),
            (select max(cast(created_at as date)) from {{ source('raw', 'orders') }}),
            current_date
        ) as d1
),
dates as (
    select cast(d as date) as rate_date
    from bounds, generate_series(d0, d1, interval 1 day) as t(d)
),
fx as (
    select rate_date, rate as eur_usd
    from {{ source('raw', 'fx_rates') }}
    where base = 'EUR' and quote = 'USD'
),
filled as (
    select
        dates.rate_date,
        last_value(fx.eur_usd ignore nulls) over (
            order by dates.rate_date
            rows between unbounded preceding and current row
        ) as last_known,
        first_value(fx.eur_usd ignore nulls) over (
            order by dates.rate_date
            rows between unbounded preceding and unbounded following
        ) as first_known
    from dates
    left join fx using (rate_date)
)
select rate_date, coalesce(last_known, first_known) as eur_usd
from filled