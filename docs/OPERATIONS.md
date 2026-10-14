# Obsługa lokalna i operacje

## Przebieg codzienny

Airflow planuje DAG na 10:30 w strefie Europe/Warsaw, po zwykłej porze publikacji
dziennego pakietu TED. Każde uruchomienie pobiera bieżący dzień oraz nakładające się
14 dni. Zakres można zmienić w DAG-u lub uruchomić z CLI.

Task ma retry z przerwą, limit czasu i jawne logi. API Search jest publiczne, dlatego
klucz API nie jest wymagany. Retry nie zastępuje idempotentnego upsertu.

## Ręczne polecenia

    docker compose ps
    docker compose logs --tail 100 airflow-scheduler
    docker compose --profile manual run --rm ingest python -m procurescope.cli ingest --days 30
    docker compose --profile manual run --rm dbt dbt build --project-dir /opt/airflow/app/dbt --profiles-dir /opt/airflow/app/dbt
    docker compose exec postgres psql -U procurescope -d procurescope -c "select status, started_at, page_count, received_count, loaded_count, rejected_count from ingestion_runs order by started_at desc limit 10;"

## Kontrola wyniku

1. Sprawdź, czy przebieg ma status=succeeded oraz oczekiwaną liczbę stron.
2. Porównaj received_count z loaded_count + rejected_count.
3. Sprawdź ostatnie rekordy w rejected_records i przyczynę odrzucenia.
4. Porównaj liczbę kluczy z source_notice_versions przed i po ponownym pobraniu
   tego samego zakresu.
5. Sprawdź manifest i SHA-256 plików z przebiegu w bucket procurescope-bronze.
6. W Metabase pokaż świeżość danych, pokrycie pól i link źródłowy, jeśli dostępny.

## Awaria i wznowienie

- Błąd API pozostawia już odebrane pliki w Bronze i oznacza run jako failed.
- Powtórz zakres z tymi samymi datami. Upsert zachowa jeden wiersz na klucz i wersję.
- Jeżeli zmienił się parser, zbuduj osobne zadanie reprocess odczytujące JSON z Bronze.
  Reprocess nie jest jeszcze osobnym poleceniem CLI w wersji 0.1.
- Błędy połączenia z MinIO/PostgreSQL należy sprawdzić przed zwiększeniem retry.
  Nie kasuj partycji Bronze po nieudanym runie.

## Kopie i sprzątanie

Wolumeny Compose postgres-data, minio-data i airflow-logs są trwałe.
docker compose down ich nie usuwa. docker compose down -v usuwa lokalną bazę,
archiwum Bronze i logi — używaj tylko wtedy, gdy chcesz zacząć od zera.

W środowisku współdzielonym ustaw unikalne hasła, ogranicz porty do sieci prywatnej,
zrób kopie PostgreSQL/MinIO i ustal retencję logów. Domyślne hasła z .env.example
przeznaczone są wyłącznie do lokalnego demo.
