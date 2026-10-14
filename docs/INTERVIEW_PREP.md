# Przygotowanie do rozmowy o ProcureScope

Mów o decyzjach, które rzeczywiście widać w kodzie. Projekt jest demonstracją
inżynierii danych; nie przypisuj mu wdrożonych oszczędności ani wpływu na użytkowników.

1. Problem? Śledzenie ogłoszeń IT, terminów i późniejszych pól wynikowych w TED.
2. Użytkownik? Mały dostawca IT lub konsultant analizujący zamówienia publiczne.
3. Decyzja? Czy w nadchodzących tygodniach są otwarte zamówienia pasujące do oferty.
4. Metryki? Strony, rekordy odebrane/załadowane/odrzucone, czas i świeżość.
5. Czy to nowy produkt rynkowy? Nie twierdzę, że rynek nie ma podobnych usług.
6. Dlaczego TED? Publiczne API Search pozwala pobierać opublikowane ogłoszenia bez klucza.
7. Czy kraj zamawiającego wystarcza? Nie; miejsce realizacji jest osobnym filtrem.
8. Dlaczego CPV 72? To rodzina usług IT; filtr jest jawny i konfigurowalny.
9. Jak nie pomijasz stron? Iteracyjny token API trafia do kolejnego zapytania.
10. Co robisz przy limicie? Strona ma najwyżej 250 dokumentów; iteracja przechodzi
    poza limit 15 tys. wyników zwykłej paginacji.
11. Co zapisujesz w Bronze? Oryginalne bajty, manifest, SHA-256, czas, zapytanie i run.
12. Co przy błędzie API? Retry dla błędów przejściowych; run nie dostaje statusu sukcesu.
13. Jak ponawiasz zakres? Powtarzam daty; nowe pliki Bronze, idempotentny upsert w Silver.
14. Jak działa przyrost? Dzienny zakres z nakładką 14 dni na opóźnienia i korekty.
15. Czy raw można przetworzyć ponownie? Bronze zachowuje oryginalne strony, ale CLI
    reprocess nie jest jeszcze zaimplementowany. Powtórny ingest ponownie odpytuje TED.
16. Co oznacza rekord? Zaobserwowaną wersję ogłoszenia, nie całe postępowanie.
17. Numer publikacji to ID? Nie zakładam; trzymam publication-number i notice-identifier.
18. Jak wygląda historia? Identyfikator i wersja budują klucz; kolejne obserwacje
    aktualizują czas ostatniej widoczności.
19. Jak łączysz korekty? Stabilnymi identyfikatorami, nie podobnym tytułem.
20. Czy modelujesz części? Zachowuję źródłowe pola; nie tworzę faktu części bez pewnego mapowania.
21. Dlaczego osobne tabele? Przebieg, ogłoszenie i odrzut mają różne ziarno.
22. Silver czy gwiazda? Silver zachowuje źródło, a dbt tworzy modele raportowe.
23. Co oznacza NULL? Może to być brak pola lub brak zastosowania, nie zawsze błąd.
24. Jak sumujesz kwoty? Nie sumuję surowych wyników bez waluty, typu wartości i ziarna.
25. Jak obsługujesz daty? Publikacja i termin to osobne pola, czas pobrania jest w UTC.
26. Co przy zmianie TED? Raw payload pozostaje; parser akceptuje różne kształty.
27. Co z błędnym rekordem? Kwarantanna zawiera powód; raw nie znika.
28. Jak unikniesz duplikatów? Unikalny notice_key i transakcyjny UPSERT.
29. Idempotencja? Ponowny zakres nie tworzy kolejnego wiersza dla tej samej wersji.
30. Gdzie potrzebna transakcja? Zapis pełnego rekordu; run sukcesem po wszystkich stronach.
31. Jakie indeksy? Publikacja, termin, buyer name i GIN na CPV.
32. Jak diagnozujesz wolny SQL? EXPLAIN (ANALYZE, BUFFERS) na danych.
33. Jakie ograniczenia w bazie? Klucz główny, status przebiegu, FK; pola opcjonalne nullable.
34. Jakie raporty? Miesięczne ogłoszenia, terminy, zamawiający i dostępność pól.
35. Co kontroluje dbt? Klucze, wymagane wartości i relacje wraz z dokumentacją.
36. Jak testować parser? Na zamrożonych próbkach, bez żywego API.
37. Jednostkowy vs integracyjny? Parser izolowany kontra zapis/odczyt z testowej bazy.
38. Jak sprawdzasz kompletność? received_count porównuję z loaded_count + rejected_count.
39. Czy każdy warning zatrzymuje pipeline? Brak ID odrzuca rekord; opcjonalne braki mierzę.
40. Co dokumentuje dbt? Źródła, znaczenie modeli, kolumny i kontrole.
41. Co jest w DAG-u? Pobranie i zapis przez Python, potem dbt build.
42. Kiedy działa harmonogram? Codziennie 10:30 Europe/Warsaw.
43. Co po błędzie API? Retry i jawny status, bez pozornego sukcesu.
44. Jak backfillujesz? Jawny zakres dat w CLI lub uruchomienie DAG dla historii.
45. Jak ograniczasz obciążenie TED? Batch, strona do 250, retry respektujące Retry-After.
46. Co po błędzie strony 4? Strony 1–3 są w Bronze, run jest failed, można powtórzyć zakres.
47. Jak mierzysz świeżość? Czas ostatniego sukcesu i publication_date.
48. Jak odtworzyć projekt? Docker Compose, .env.example i polecenia z README.
49. Jak chronisz sekrety/licencję? .env jest ignorowane, MIT dotyczy kodu, TED ma własne warunki.
50. Jakie ograniczenia wskażesz? Brak heurystycznego łączenia, walut i dowiedzionego ROI.

## Demo na żywo

1. Uruchom krótki zakres.
2. Pokaż stronę i manifest w MinIO.
3. Powtórz zakres i porównaj liczbę wierszy po kluczu.
4. Pokaż przebieg i odrzucone rekordy.
5. Otwórz model w Metabase i przejdź od liczby do źródłowego TED.

Jeśli próbka nie zawiera błędnych rekordów, nie twórz pozornej awarii ani
niepopartego przykładu biznesowego.
