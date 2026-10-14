-- Ręczny przegląd najnowszych przebiegów.
select *
from public.ingestion_runs
order by started_at desc
limit 20;

-- Porównanie liczby odebranych elementów z liczbą poprawnych i odrzuconych.
select
    run_id,
    received_count,
    loaded_count,
    rejected_count,
    received_count - loaded_count - rejected_count as unexplained_difference
from public.ingestion_runs
where status = 'succeeded'
order by started_at desc;

-- Rekordy wymagające uwagi parsera.
select run_id, page_number, reason, count(*) as record_count
from public.rejected_records
group by run_id, page_number, reason
order by run_id desc, record_count desc;

-- Przykładowe pokrycie w tabeli źródłowej bez usuwania pustych danych.
select
    count(*) as notice_versions,
    count(*) filter (where deadline is not null) as with_deadline,
    count(*) filter (where buyer_name is not null) as with_buyer,
    count(*) filter (where notice_url is not null) as with_source_link
from public.source_notice_versions;
