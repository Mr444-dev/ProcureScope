# ProcureScope

**Hurtownia danych o publicznych przetargach IT z miejscem realizacji w Polsce.**
ProcureScope pobiera ogłoszenia z TED, archiwizuje niezmienioną odpowiedź API, zapisuje
uporządkowane rekordy w PostgreSQL i buduje modele analityczne przez dbt. Airflow
uruchamia codzienny przyrost, a Metabase udostępnia gotowe zapytania do raportów.

> To projekt portfolio do monitorowania i analizy danych. Nie składa ofert, nie jest
> poradą prawną i nie gwarantuje kompletności rynku. Każdy rekord prowadzi z powrotem
> do widoku źródłowego TED, jeśli rekord ma numer publikacji.

## Co jest już w repozytorium

- klient TED Search API v3 z iteracyjnym pobieraniem, retry i zachowaniem stron;
- niezmienne pliki Bronze JSON oraz manifest z zapytaniem, czasem i SHA-256;
- tabela wersji ogłoszeń, historia przebiegów i kwarantanna błędnych rekordów;
- deterministyczne klucze i UPSERT, żeby ponowne uruchomienie nie tworzyło kopii;
- modele dbt dla szans IT, zamawiających, aktywności oraz dostępności danych o wynikach;
- harmonogram Airflow, lokalne środowisko Docker Compose i konfiguracja Metabase;
- dokumentacja architektury, modelu danych, obsługi, źródeł i przygotowania do rozmowy.

## Architektura

    TED Search API v3 -> Python: pobieranie i walidacja -> MinIO: niezmienne odpowiedzi JSON
                                                    -> PostgreSQL: ogłoszenia i kwarantanna
    Airflow: harmonogram -> Python -> dbt: modele analityczne -> Metabase: raporty

Przebieg zapisuje każdą odebraną stronę **przed parsowaniem**. Błąd parsera trafia do
rejected_records, a źródłowy JSON pozostaje w Bronze. Zmiana parsera nie wymaga
ponownego odpytywania TED. W razie przerwania pobrania przebieg otrzymuje status
failed; rozpoczęte strony pozostają dostępne do audytu.

## Uruchomienie lokalne

Wymagane są Docker Desktop z Compose v2 oraz dostęp do Internetu. W PowerShell:

    Set-Location outputs/ProcureScope
    Copy-Item .env.example .env

Zmień hasła w .env przed startem. Po zmianie hasła PostgreSQL zaktualizuj
POSTGRES_PASSWORD, DATABASE_URL i AIRFLOW__DATABASE__SQL_ALCHEMY_CONN w .env.
Compose przekazuje hasło do Metabase i dbt. Po zmianie hasła MinIO zaktualizuj
S3_SECRET_KEY.

Uruchom podstawowe usługi:

    docker compose up --build -d
    docker compose ps

Interfejsy lokalne:

| Usługa | Adres | Dane demo |
|---|---|---|
| Airflow | http://localhost:8080 | użytkownik i hasło z .env |
| Metabase | http://localhost:3000 | pierwsza konfiguracja w przeglądarce |
| MinIO Console | http://localhost:9001 | wartości MINIO_ROOT_USER i MINIO_ROOT_PASSWORD |
| PostgreSQL | localhost:5432 | baza procurescope |

W Airflow włącz DAG procurescope_daily, aby uruchomić harmonogram. Jednorazowy
backfill można wykonać bez czekania na scheduler:

    docker compose --profile manual run --rm ingest python -m procurescope.cli ingest --days 548

Po pobraniu i zapisaniu danych zbuduj modele:

    docker compose --profile manual run --rm dbt

Polecenie może pobrać duży zakres z TED. Krótszy, jawny zakres do pierwszego przebiegu:

    docker compose --profile manual run --rm ingest python -m procurescope.cli ingest --from-date 2026-10-01 --to-date 2026-10-14

Daty są włączne. API TED udostępnia publiczne wyszukiwanie bez klucza API. Repozytorium
nie zawiera tokenów ani skopiowanych zbiorów TED.

### Pierwsze połączenie Metabase

Podczas konfiguracji Metabase dodaj bazę PostgreSQL:

- host: postgres
- port: 5432
- baza: procurescope
- użytkownik i hasło: z .env
- schemat: analytics (modele dbt) lub public (tabele źródłowe)

Gotowe zapytania do dashboardu znajdują się w metabase/questions.sql. Możesz je wkleić
jako pytania SQL i ułożyć w dashboard: „Otwarte terminy”, „Aktywność zamawiających”
oraz „Pokrycie danych”.

## Polecenia developerskie

Do lokalnego uruchamiania poza Dockerem zainstaluj projekt i ustaw własne adresy
PostgreSQL/MinIO w środowisku:

    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -e .
    $env:DATABASE_URL = "postgresql://procurescope:haslo@localhost:5432/procurescope"
    $env:STORAGE_BACKEND = "local"
    procurescope init-db
    procurescope ingest --from-date 2026-10-01 --to-date 2026-10-14

Quality gate w GitHub Actions uruchamia Ruff i sprawdza kompilację modułów Pythona.
Kontrole danych dbt są opisane przy modelach; uruchamia je dbt build.

## Zakres i świadome ograniczenia

- Zakres domyślny to daty publikacji, rodzina CPV 72* i miejsce realizacji POL.
  Kraj zamawiającego pozostaje osobnym polem.
- publication-number, notice-identifier i wersja są przechowywane oddzielnie.
  Klucz rekordu budowany jest z identyfikatora źródła i wersji; bezpieczne połączenie
  ogłoszeń w jedno postępowanie korzysta wyłącznie z procedure_identifier.
- Rozstrzygnięcia są zachowane jako pola źródłowe, jeśli API je zwróci. Wartości
  szacunkowe i wartości udzielonych zamówień nie są sumowane. award_fields jest
  surowym podsumowaniem dostępnych pól wynikowych, a nie znormalizowanym faktem na
  poziomie części.
- Różne waluty nie są przeliczane. Puste pola mogą być zgodne z typem ogłoszenia i
  nie są automatycznie usuwane.
- TED zawiera formularze eForms i starsze formularze. Parser przyjmuje niejednorodne
  wartości, ale Silver zachowuje pełny rekord źródłowy, by umożliwić ponowną analizę.
- Okno przyrostu i ponownego sprawdzenia można zmienić przez przekazanie zakresu
  dat; dzienny DAG ponownie pobiera ostatnie 14 dni.
- Połączenie zamawiających po nazwie nie jest tożsamością prawną. Raporty grupują
  po nazwie i kraju wyłącznie dla wygody.

Szczegóły: docs/ARCHITECTURE.md, docs/DATA_DICTIONARY.md i docs/OPERATIONS.md.

## Źródła i atrybucja

ProcureScope korzysta z publicznego TED Search API. Zachowaj atrybucję do TED przy
ponownym wykorzystaniu jego danych i sprawdź aktualne warunki TED przed komercyjnym
wdrożeniem.

- [TED Search API v3](https://docs.ted.europa.eu/api/latest/search.html)
- [Pobieranie danych i tryby stronicowania](https://docs.ted.europa.eu/ODS/latest/reuse/search-api.html)
- [Lista pól wyszukiwarki TED](https://docs.ted.europa.eu/ODS/latest/reuse/field-list.html)
- [Pomoc TED: składnia wyszukiwania eksperckiego](https://ted.europa.eu/en/help/search-browse)
- [Klasyfikacja CPV](https://docs.ted.europa.eu/eforms/latest/reference/code-lists/cpv.html)
- [Ponowne wykorzystanie danych TED](https://docs.ted.europa.eu/ODS/latest/reuse/index.html)

Kod projektu jest udostępniony na licencji MIT. Licencja kodu nie zmienia warunków,
na których udostępniane są dane zewnętrzne. Zobacz NOTICE.

## Współtworzenie

Zgłoszenia i poprawki są mile widziane. Przed pull requestem przeczytaj
CONTRIBUTING.md. Zasady zgłaszania problemów bezpieczeństwa opisuje SECURITY.md.
