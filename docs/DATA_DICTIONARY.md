# Słownik danych

## public.ingestion_runs

Jeden wiersz oznacza jedno wywołanie pipeline'u dla danego zakresu i zapytania.

| Kolumna | Znaczenie |
|---|---|
| run_id | UUID przebiegu, używany również w ścieżce Bronze |
| query_text | Pełne zapytanie przekazane do TED |
| window_start, window_end | Włączne granice dat publikacji |
| started_at, finished_at | Czas startu i zakończenia w UTC |
| status | running, succeeded albo failed |
| page_count | Liczba stron odebranych z API |
| received_count | Liczba obiektów zwróconych w stronach |
| loaded_count | Liczba rekordów poprawnie zapisanych/upsertowanych |
| rejected_count | Liczba rekordów skierowanych do kwarantanny |
| error_message | Ograniczony komunikat błędu nieudanego przebiegu |

## public.source_notice_versions

Jeden wiersz odpowiada zaobserwowanej wersji ogłoszenia. To niekoniecznie to samo co
jedno postępowanie, część lub wynik. Klucz obcy do źródłowego przebiegu wskazuje
ostatni przebieg, który załadował tę wersję; first_seen_at zachowuje pierwsze
zaobserwowanie.

| Kolumna | Znaczenie |
|---|---|
| notice_key | Lokalny, deterministyczny klucz techniczny |
| publication_number | Numer publikacji TED, jeśli zwrócony |
| notice_identifier | Identyfikator ogłoszenia, osobny od numeru publikacji |
| notice_version | Wersja źródłowa, jeśli występuje |
| publication_date | Data publikacji |
| title | Wybrany tytuł z pola ogłoszenia |
| buyer_name, buyer_country | Nazwa i kraj zamawiającego |
| deadline | Dostępny termin składania ofert |
| cpv_codes | Kody CPV zwrócone dla ogłoszenia, jako tablica JSON |
| performance_locations | Lokacje realizacji zwrócone przez TED, jako tablica JSON |
| procedure_identifier | Identyfikator procedury, jeśli dostępny |
| form_type | Rodzaj formularza/ogłoszenia |
| notice_url | Link do widoku ogłoszenia TED, zbudowany z numeru publikacji |
| award_fields | Surowe wybrane pola wyniku; bez sumowania wartości |
| source_hash | SHA-256 kanonicznej reprezentacji obiektu wyniku |
| source_payload | Pełny pojedynczy obiekt z odpowiedzi Search API |
| ingestion_run_id | Ostatni przebieg ładujący wersję |
| first_seen_at, last_seen_at, updated_at | Znaczniki obserwacji/aktualizacji w UTC |

## public.rejected_records

Jeden wiersz oznacza rekord z odpowiedzi TED, którego nie można było bezpiecznie
znormalizować. source_payload zachowuje obiekt źródłowy, reason wyjaśnia brak
identyfikatora lub typ innego błędu.

## Modele analityczne analytics

| Model | Ziarno i zawartość |
|---|---|
| stg_source_notices | Jeden wiersz na wersję ogłoszenia, uporządkowane typy z Silver |
| fct_it_opportunities | Jedna wersja ogłoszenia z CPV zaczynającym się od 72 |
| dim_buyer | Para nazwa zamawiającego + kraj, identyfikator wyłącznie raportowy |
| mart_buyer_activity | Liczba wersji ogłoszeń IT według zamawiającego i miesiąca |
| mart_award_notice_coverage | Ogłoszenia z polami wynikowymi wraz z surowym JSON |
| mart_data_coverage | Liczba i odsetek rekordów z dostępnymi kluczowymi polami |

Nie należy sumować wartości z award_fields bez rozdzielenia waluty, rodzaju
wartości (szacunkowa vs udzielona) i poziomu (ogłoszenie vs część).
