select
    notice_key,
    publication_number,
    publication_date,
    buyer_name,
    buyer_country,
    notice_url,
    award_fields
from {{ ref('stg_source_notices') }}
where award_fields <> '{}'::jsonb
