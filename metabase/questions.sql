-- 1. Terminy dziś lub w ciągu najbliższych 30 dni.
select publication_number, title, buyer_name, buyer_country, deadline,
       days_until_deadline, cpv_codes, notice_url
from analytics.mart_upcoming_deadlines
where days_until_deadline between 0 and 30
order by deadline asc;

-- 2. Aktywność zamawiających według miesiąca; nazwa nie jest prawnym ID.
select month, buyer_name, buyer_country, notice_versions
from analytics.mart_buyer_activity
order by month desc, notice_versions desc;

-- 3. Dostępność podstawowych pól.
select * from analytics.mart_data_coverage;

-- 4. Ogłoszenia z polami wynikowymi. Kwoty pozostają w źródłowej walucie/ziarnie.
select publication_number, buyer_name, publication_date, award_fields, notice_url
from analytics.mart_award_notice_coverage
order by publication_date desc;

-- 5. Treść źródłowa dodana lub zmieniona w TED w ostatnich 30 dniach.
-- source_changed_at nie zmienia się przy samym ponownym pobraniu tej samej treści.
select publication_number, title, buyer_name, publication_date,
       source_changed_at, notice_url
from analytics.fct_it_opportunities
where source_changed_at >= now() - interval '30 days'
order by source_changed_at desc;

-- 6. Ostatnie przebiegi pipeline'u.
select run_id, status, started_at, finished_at, page_count,
       received_count, loaded_count, rejected_count, error_message
from public.ingestion_runs
order by started_at desc
limit 20;
