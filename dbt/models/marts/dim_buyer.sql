select
    md5(lower(trim(buyer_name)) || '|' || coalesce(upper(trim(buyer_country)), '')) as buyer_key,
    max(trim(buyer_name)) as buyer_name,
    upper(trim(buyer_country)) as buyer_country,
    count(*) as observed_notice_versions
from {{ ref('fct_it_opportunities') }}
where buyer_name is not null
group by lower(trim(buyer_name)), upper(trim(buyer_country))
