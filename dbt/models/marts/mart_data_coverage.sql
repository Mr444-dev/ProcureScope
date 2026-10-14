with summary as (
    select
        count(*) as total_notices,
        count(*) filter (where title is not null) as with_title,
        count(*) filter (where buyer_name is not null) as with_buyer,
        count(*) filter (where deadline is not null) as with_deadline,
        count(*) filter (where jsonb_array_length(cpv_codes) > 0) as with_cpv,
        count(*) filter (where jsonb_array_length(performance_locations) > 0) as with_place,
        count(*) filter (where award_fields <> '{}'::jsonb) as with_award_fields
    from {{ ref('stg_source_notices') }}
)

select
    total_notices,
    with_title,
    with_buyer,
    with_deadline,
    with_cpv,
    with_place,
    with_award_fields,
    round(100.0 * with_title / nullif(total_notices, 0), 1) as title_coverage_pct,
    round(100.0 * with_buyer / nullif(total_notices, 0), 1) as buyer_coverage_pct,
    round(100.0 * with_deadline / nullif(total_notices, 0), 1) as deadline_coverage_pct,
    round(100.0 * with_cpv / nullif(total_notices, 0), 1) as cpv_coverage_pct,
    round(100.0 * with_place / nullif(total_notices, 0), 1) as place_coverage_pct,
    round(100.0 * with_award_fields / nullif(total_notices, 0), 1) as award_field_coverage_pct
from summary
