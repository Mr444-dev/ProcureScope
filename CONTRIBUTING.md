# Współtworzenie

Dziękujemy za zainteresowanie ProcureScope. Małe, konkretne pull requesty ułatwiają
przegląd zmian w parserze i modelach danych.

## Zasady zmian

1. Opisz problem i oczekiwany efekt.
2. Przy zmianie mapowania TED wskaż nazwę pola źródłowego, jego znaczenie i przykład
   bez danych wrażliwych.
3. Nie dodawaj tokenów, haseł, danych z prywatnych kont ani dużych zrzutów TED.
4. Aktualizuj słownik danych i ograniczenia, gdy zmienia się semantyka modelu.
5. Uruchom ruff check src airflow i dbt build na środowisku z danymi testowymi,
   jeśli zmiana dotyczy modeli SQL.

## Pull request

Dołącz opis zmiany, ryzyka dla jakości danych i sposób ręcznej weryfikacji. Nie
deklaruj kompletności danych ani efektu biznesowego bez pomiaru.
