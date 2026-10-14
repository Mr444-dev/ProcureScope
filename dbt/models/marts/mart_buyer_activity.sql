select
    date_trunc('month', publication_date)::date as month,
    buyer_name,
    buyer_country,
    count(*) as notice_versions,
    count(distinct publication_number) as publication_numbers
from {{ ref('fct_it_opportunities') }}
where publication_date is not null
  and buyer_name is not null
group by 1, 2, 3
