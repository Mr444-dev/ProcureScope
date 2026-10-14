with notices as (
    select *
    from {{ ref('stg_source_notices') }}
)

select
    notice_key,
    publication_number,
    notice_identifier,
    notice_version,
    publication_date,
    title,
    buyer_name,
    buyer_country,
    deadline,
    cpv_codes,
    performance_locations,
    procedure_identifier,
    form_type,
    notice_url,
    case
        when deadline is null then 'unknown'
        when deadline < current_date then 'deadline_passed'
        else 'deadline_open'
    end as deadline_status,
    award_fields <> '{}'::jsonb as has_award_fields,
    ingestion_run_id,
    first_seen_at,
    last_seen_at,
    source_changed_at,
    updated_at
from notices
where exists (
    select 1
    from jsonb_array_elements_text(notices.cpv_codes) as cpv(code)
    where cpv.code like '72%'
)
