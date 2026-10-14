select
    notice_key,
    publication_number,
    title,
    buyer_name,
    buyer_country,
    deadline,
    deadline - current_date as days_until_deadline,
    cpv_codes,
    performance_locations,
    notice_url,
    source_changed_at
from {{ ref('fct_it_opportunities') }}
where deadline >= current_date
