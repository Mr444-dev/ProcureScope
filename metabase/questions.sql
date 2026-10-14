-- 1. Otwarte terminy w najbliższych 30 dniach.
select publication_number, title, buyer_name, buyer_country, deadline, cpv_codes, notice_url
from analytics.fct_it_opportunities
where deadline >= current_date
  and deadline < current_date + interval '30 days'
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

-- 5. Ostatnie przebiegi pipeline'u.
select run_id, status, started_at, finished_at, page_count,
       received_count, loaded_count, rejected_count, error_message
from public.ingestion_runs
order by started_at desc
limit 20;
