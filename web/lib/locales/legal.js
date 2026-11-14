// Rechtliche Seiten / Strony prawne / Právní stránky – deutsch, polnisch, tschechisch.
// Inhaltlich identisch mit der ungarischen/englischen Fassung in lib/legal.js (dort: Betreiberdaten, Dienstleister).
// H: gemeinsame Bausteine aus lib/legal.js (operatorLines, hosts, usNote, US_BASIS, ADS_ON, COFFEE_URL, SITE_NAME …).

export function legalX(H) {
  const { operatorLines, hosts, usNote, US_BASIS, ADS_ON, COFFEE_URL, SITE_NAME: S, SITE_URL, LEGAL_UPDATED: U, O } = H;
  const coffeeHost = COFFEE_URL ? new URL(COFFEE_URL).hostname : "";
  const NAIH = "NAIH, 1055 Budapest, Falk Miksa utca 9–11, www.naih.hu";

  // ───────────────────────────── DEUTSCH ─────────────────────────────
  const de = {
    terms: [
      { p: [`Gültig ab: ${U}. Diese Bedingungen regeln die Nutzung der Website ${S} (${SITE_URL}). Mit der Nutzung der Website erkennt der Nutzer diese Bedingungen an.`] },
      { h: "1. Betreiber", list: operatorLines("de") },
      { h: "2. Der Dienst", p: [
        `${S} ist ein kostenloser, rein informativer Preis- und Verfügbarkeitsvergleich für Airsoft-Produkte. Die Website ist kein Onlineshop: Sie verkauft keine Produkte, nimmt keine Bestellungen an und wickelt keine Zahlungen ab.`,
        "Ein Kauf kommt ausschließlich zwischen dem Nutzer und dem gewählten Shop zu dessen eigenen Bedingungen zustande. Die Website ist an diesem Vertragsverhältnis nicht beteiligt und haftet nicht für die Leistungen der Shops (Lieferung, Gewährleistung, Widerruf, Reklamationen).",
      ] },
      { h: "3. Preise und Richtigkeit der Daten", list: [
        "Preise, Verfügbarkeit und Produktdaten werden einmal täglich automatisch von den öffentlichen Seiten der Shops erfasst und können daher von den aktuellen Angaben des Shops abweichen.",
        "Die angezeigten Preise enthalten keine Versandkosten. Shop-Preise in anderen Währungen (z. B. HUF, PLN) werden zum Tageskurs der Ungarischen Nationalbank (MNB) in die gewählte Währung umgerechnet; der Endbetrag im Shop kann davon abweichen.",
        "Die Zuordnung der Produkte erfolgt automatisch; es kann vorkommen, dass unterschiedliche Varianten (Farbe, Ausführung) unter einem Produkt erscheinen.",
        "Maßgeblich sind vor dem Kauf stets die Angaben auf der Website des Shops.",
      ] },
      { h: "4. Externe Links und Partnerprogramme", p: [
        "Die Schaltfläche „Zum Shop“ führt auf die Website des Shops. Einige Links können Partnerlinks (Affiliate-Links) sein: Kauft der Nutzer über einen solchen Link, kann der Betreiber eine Provision erhalten. Dies hat keinen Einfluss auf den vom Nutzer gezahlten Preis und auch nicht auf die Reihenfolge der Ergebnisse, die nach Preis, Anzahl der Shops oder Name sortiert werden.",
      ] },
      { h: "5. Hinweis zu Airsoft-Produkten", list: [
        "Kauf, Besitz und Transport von Airsoft-Waffen sind in jedem Land unterschiedlich geregelt (z. B. Altersgrenzen, Energiegrenzen, Versandverbote). Für die Einhaltung dieser Vorschriften ist der Nutzer selbst verantwortlich.",
        "Minderjährige dürfen Airsoft-Waffen nur im Rahmen der örtlichen Gesetze und der Bedingungen des Shops kaufen; viele Shops verkaufen nur an Personen ab 18 Jahren.",
        "Halte beim Spielen die örtlichen Sicherheitsregeln ein, insbesondere zum Augenschutz.",
      ] },
      { h: "6. Geistiges Eigentum", p: [
        "Produkt- und Markennamen sowie Logos sind Eigentum ihrer jeweiligen Inhaber; sie werden ausschließlich zur Identifizierung der Produkte angezeigt. Produktbilder sind Eigentum der Shops bzw. der Hersteller und werden zur Darstellung des Angebots des jeweiligen Shops angezeigt.",
        "Die eigenen Inhalte der Website (Gestaltung, Texte, zusammengeführte Daten) dürfen ohne Erlaubnis des Betreibers weder massenhaft kopiert noch mit automatisierten Mitteln erfasst werden.",
      ] },
      { h: "7. Haftungsbeschränkung", p: [
        "Der Betreiber bemüht sich um einen ununterbrochenen und fehlerfreien Betrieb der Website, kann diesen jedoch nicht garantieren. Soweit gesetzlich zulässig, haftet der Betreiber nicht für Schäden, die aus der Nutzung der Daten der Website, aus ihrer Nichterreichbarkeit oder aus Vertragsverhältnissen mit den Shops entstehen.",
      ] },
      { h: "8. Shops und Rechteinhaber", p: [
        `Möchte ein Shop nicht auf der Website erscheinen oder stellt er fehlerhafte Daten fest, kann er unter ${O.email} eine Korrektur oder Entfernung verlangen. Einzelheiten auf der Seite „Für Händler“.`,
      ] },
      { h: "9. Schlussbestimmungen", p: [
        "Der Betreiber ist berechtigt, diese Bedingungen einseitig zu ändern; Änderungen treten mit ihrer Veröffentlichung auf dieser Seite in Kraft. Es gilt ungarisches Recht; zwingende Verbraucherschutzvorschriften des Staates, in dem der Verbraucher seinen gewöhnlichen Aufenthalt hat, bleiben unberührt. Bei Fragen schreibe an die oben genannte E-Mail-Adresse.",
      ] },
    ],
    privacy: [
      { p: [`Gültig ab: ${U}. Diese Erklärung beschreibt auf Grundlage der Datenschutz-Grundverordnung der Europäischen Union (DSGVO, Verordnung (EU) 2016/679), wie ${S} die Daten seiner Besucher verarbeitet.`] },
      { h: "1. Verantwortlicher", list: operatorLines("de") },
      { h: "2. Kurz gesagt", list: [
        "Auf der Website gibt es keine Registrierung. Personenbezogene Daten (eine E-Mail-Adresse) erfragen wir nur, wenn du eine Preis- oder Verfügbarkeitsbenachrichtigung anforderst.",
        ADS_ON ? "Wir verwenden keine Analyse-Cookies. Werbe-Cookies können nur von den Anzeigen von Google gesetzt werden, und nur mit deiner Einwilligung (siehe unten)." : "Wir verwenden keine Analyse-, Tracking- oder Werbe-Cookies.",
        ADS_ON ? "Wir setzen selbst nur ein einziges Cookie: um die gewählte Währung zu speichern." : "Wir verwenden ein einziges Cookie: um die gewählte Währung zu speichern.",
      ] },
      { h: "3. Welche Daten wir verarbeiten", list: [
        "Technische Protokolldaten: Beim Aufruf einer Seite speichert der Server des Hosting-Anbieters (Cloudflare) automatisch die IP-Adresse, den Browsertyp, die aufgerufene Seite und den Zeitpunkt. Zweck: sicherer Betrieb der Website, Fehlersuche, Abwehr von Missbrauch. Rechtsgrundlage: berechtigtes Interesse (Art. 6 Abs. 1 lit. f DSGVO). Speicherdauer: gemäß der Protokollierungsdauer des Hosting-Anbieters, höchstens einige Wochen.",
        "Währungs-Cookie („cur“): speichert die vom Nutzer gewählte Währung (z. B. EUR, HUF) für 1 Jahr. Es ist für die angeforderte Funktion unbedingt erforderlich und enthält keine personenbezogenen Daten, daher ist keine Einwilligung nötig.",
        "Externe Links: Die Schaltfläche „Zum Shop“ leitet über die Adresse /go/… zum Shop weiter. Dabei speichern wir keine personenbezogenen Daten. Auf der Website des Shops gilt dessen eigene Datenschutzerklärung.",
        "Kontaktaufnahme: Wenn du uns eine E-Mail schreibst, verwenden wir deinen Namen, deine E-Mail-Adresse und deine Nachricht zur Beantwortung der Anfrage und speichern sie nach Abschluss des Vorgangs höchstens 1 Jahr. Rechtsgrundlage: berechtigtes Interesse.",
      ] },
      { h: "Preis- und Verfügbarkeitsbenachrichtigung (E-Mail)", list: [
        "Wenn du auf einer Produktseite eine Benachrichtigung anforderst, verarbeiten wir: deine E-Mail-Adresse, das Produkt, die Art der Benachrichtigung (wieder auf Lager / Zielpreis), den Zielpreis und seine Währung, den Zeitpunkt der Anfrage, der Bestätigung und des Versands sowie einen einseitigen, gekürzten Hashwert deiner IP-Adresse zur Abwehr von Missbrauch (massenhafte Anmeldungen).",
        "Zweck: Versand der angeforderten Benachrichtigung. Rechtsgrundlage: Einwilligung (Art. 6 Abs. 1 lit. a DSGVO), die du durch Klick auf den Link in der Bestätigungs-E-Mail erteilst (Double-Opt-in). Ohne Bestätigung senden wir keinerlei E-Mails.",
        "Du kannst deine Einwilligung jederzeit über den Abmeldelink in unseren E-Mails (für eine oder alle Benachrichtigungen) oder über die oben genannte E-Mail-Adresse widerrufen.",
        "Speicherdauer: Nicht bestätigte Anfragen werden nach 7 Tagen, erfüllte (versandte) Benachrichtigungen nach 30 Tagen und alle übrigen Benachrichtigungen spätestens nach 1 Jahr automatisch gelöscht.",
        "Wir verkaufen die Daten nicht und nutzen sie weder für Werbung noch für Newsletter; wir senden nur die angeforderte Benachrichtigung. Die E-Mails werden von dem unten genannten E-Mail-Dienstleister zugestellt.",
      ] },
      ...(ADS_ON ? [{ h: "Werbung (Google AdSense)", list: [
        "Der Betrieb der Website wird durch Anzeigen unterstützt, die von Google AdSense ausgeliefert werden. Wir verwenden keine Pop-ups und keine automatischen Anzeigen; Anzeigen sind mit „Anzeige“ gekennzeichnet und erscheinen am Ende der Listen und Produktseiten.",
        "In der EU fragt dich das Einwilligungsfenster von Google (von Google zertifiziert, gemäß IAB TCF) beim ersten Besuch, ob du Werbe-Cookies und personalisierte Anzeigen erlaubst. Ohne Einwilligung werden nur nicht personalisierte oder eingeschränkte Anzeigen angezeigt. Rechtsgrundlage: Einwilligung (Art. 6 Abs. 1 lit. a DSGVO); du kannst deine Entscheidung jederzeit über die Datenschutzeinstellungen am Ende der Seite ändern.",
        "Google kann zur Auslieferung der Anzeigen Cookies und Gerätekennungen verwenden und Daten auf Grundlage des EU-US Data Privacy Framework in die USA übermitteln. Einzelheiten: policies.google.com/technologies/ads; personalisierte Anzeigen deaktivieren: adssettings.google.com.",
      ] }] : []),
      ...(COFFEE_URL ? [{ h: "Unterstützung („Spendiere mir einen Kaffee“)", p: [
        `Der Link am Ende der Seite führt zu einer externen Unterstützerseite (${coffeeHost}). Die Unterstützung ist freiwillig; die Zahlung und die dafür nötigen Daten verarbeitet dieser Anbieter nach seiner eigenen Datenschutzerklärung. Von ihm können wir den angegebenen Namen und die Nachricht des Unterstützers erhalten.`,
      ] }] : []),
      { h: "4. Auftragsverarbeiter und Dienstleister", list: hosts("de") },
      { p: [usNote("de") + US_BASIS.de] },
      { h: "5. Deine Rechte", p: [
        "Du kannst Auskunft über die zu deiner Person verarbeiteten Daten sowie deren Berichtigung, Löschung oder die Einschränkung der Verarbeitung verlangen und der auf berechtigtem Interesse beruhenden Verarbeitung widersprechen. Daten, die wir aufgrund deiner Einwilligung verarbeiten (Benachrichtigungen), erhältst du auf Wunsch auch in einem maschinenlesbaren Format (Datenübertragbarkeit); deine Einwilligung kannst du jederzeit widerrufen. Sende deine Anfrage an die oben genannte E-Mail-Adresse; wir antworten innerhalb von 30 Tagen.",
        `Du kannst dich bei der Datenschutz-Aufsichtsbehörde deines Wohnsitzlandes (in Deutschland bei der zuständigen Landesdatenschutzbehörde, in Österreich bei der Datenschutzbehörde) oder bei der ungarischen Datenschutzbehörde (${NAIH}) beschweren oder ein Gericht anrufen.`,
      ] },
      { h: "6. Änderungen", p: ["Wir können diese Erklärung ändern; die jeweils aktuelle Fassung ist immer auf dieser Seite abrufbar."] },
    ],
    imprint: [
      { h: "Betreiber", list: operatorLines("de") },
      { h: "Hosting-Anbieter", list: hosts("de") },
      { h: "Über die Website", p: [
        `${S} ist ein unabhängiger Airsoft-Preisvergleich. Die Website steht in keiner Verbindung zu den aufgeführten Shops und Herstellern, außer wenn bei einem Link ein Partnerprogramm besteht (siehe Nutzungsbedingungen, Abschnitt 4).`,
      ] },
    ],
    shops: [
      { p: [`${S} erfasst einmal täglich von den öffentlichen Produktseiten der Shops den Namen, den Preis, die Währung, die Verfügbarkeit, die Marke, den Produktcode und die Bildadresse und verlinkt bei jedem Angebot auf die eigene Seite des Shops.`] },
      { h: "Wie wir Daten erfassen", list: [
        "Unser Crawler heißt AirsoftHunterBot (Einzelheiten: /bot).",
        "Wir beachten die robots.txt, einschließlich des Crawl-delay-Werts.",
        "Pro Shop senden wir jeweils nur eine Anfrage, mit Pausen von 2–3 Sekunden, nachts.",
        "Wir lesen nur öffentliche Produktdaten gemäß schema.org.",
      ] },
      { h: "Korrektur, Entfernung, Zusammenarbeit", list: [
        `Fehlerhafte Daten oder Wunsch nach Entfernung: ${O.email}`,
        "Crawler sperren: User-agent: AirsoftHunterBot / Disallow: / in der robots.txt.",
        "Wenn du einen Produkt-Feed (XML/CSV) oder ein Partnerprogramm anbietest, stellen wir gern darauf um: So werden die Daten genauer und aktueller, und dein Server wird weniger belastet.",
      ] },
    ],
  };

  // ───────────────────────────── POLSKI ─────────────────────────────
  const pl = {
    terms: [
      { p: [`Obowiązuje od: ${U}. Niniejszy regulamin określa zasady korzystania z serwisu ${S} (${SITE_URL}). Korzystając z serwisu, Użytkownik akceptuje te zasady.`] },
      { h: "1. Operator", list: operatorLines("pl") },
      { h: "2. Usługa", p: [
        `${S} to bezpłatna porównywarka cen i dostępności produktów airsoftowych o charakterze wyłącznie informacyjnym. Serwis nie jest sklepem internetowym: nie sprzedaje produktów, nie przyjmuje zamówień i nie obsługuje płatności.`,
        "Umowa kupna zawierana jest wyłącznie między Użytkownikiem a wybranym sklepem, na warunkach tego sklepu. Serwis nie jest stroną tej umowy i nie odpowiada za jej wykonanie przez sklep (dostawa, gwarancja, odstąpienie od umowy, reklamacje).",
      ] },
      { h: "3. Ceny i dokładność danych", list: [
        "Ceny, informacje o dostępności i dane produktów są zbierane automatycznie raz dziennie z publicznych stron sklepów, dlatego mogą różnić się od aktualnych danych sklepu.",
        "Podane ceny nie obejmują kosztów wysyłki. Ceny sklepów podane w innych walutach (np. EUR, HUF) przeliczamy na wybraną walutę po dziennym kursie Węgierskiego Banku Narodowego (MNB); kwota końcowa w sklepie może się od nich różnić.",
        "Produkty są łączone automatycznie; może się zdarzyć, że różne warianty (kolor, wykonanie) pojawią się przy jednym produkcie.",
        "Przed zakupem zawsze wiążące są informacje podane na stronie sklepu.",
      ] },
      { h: "4. Linki wychodzące i programy partnerskie", p: [
        "Przycisk „Zobacz w sklepie” prowadzi na stronę sklepu. Niektóre linki mogą być linkami partnerskimi (afiliacyjnymi): jeśli Użytkownik dokona za ich pośrednictwem zakupu, operator może otrzymać prowizję. Nie wpływa to na cenę płaconą przez Użytkownika ani na kolejność wyników, które są sortowane według ceny, liczby sklepów lub nazwy.",
      ] },
      { h: "5. Ostrzeżenie dotyczące produktów ASG", list: [
        "Zakup, posiadanie i przewóz replik ASG podlegają w każdym kraju innym przepisom (np. ograniczenia wiekowe, limity energii, zakazy wysyłki). Za ich przestrzeganie odpowiada Użytkownik.",
        "Osoby niepełnoletnie mogą kupować repliki ASG wyłącznie zgodnie z lokalnymi przepisami i warunkami sklepu; wiele sklepów sprzedaje tylko osobom, które ukończyły 18 lat.",
        "Podczas gry przestrzegaj lokalnych zasad bezpieczeństwa, zwłaszcza dotyczących ochrony oczu.",
      ] },
      { h: "6. Własność intelektualna", p: [
        "Nazwy produktów i marek oraz logotypy należą do ich właścicieli; są wyświetlane wyłącznie w celu identyfikacji produktów. Zdjęcia produktów należą do sklepów lub producentów i są wyświetlane w celu prezentacji oferty danego sklepu.",
        "Własnych treści serwisu (szata graficzna, teksty, zestawione dane) nie wolno masowo kopiować ani pobierać za pomocą narzędzi automatycznych bez zgody operatora.",
      ] },
      { h: "7. Ograniczenie odpowiedzialności", p: [
        "Operator dokłada starań, aby serwis działał nieprzerwanie i bezbłędnie, ale tego nie gwarantuje. W zakresie dopuszczalnym przez prawo operator nie odpowiada za szkody wynikające z korzystania z danych serwisu, jego niedostępności ani z umów zawartych ze sklepami.",
      ] },
      { h: "8. Sklepy i podmioty uprawnione", p: [
        `Jeśli sklep nie chce być prezentowany w serwisie lub zauważy błędne dane, może zażądać poprawienia lub usunięcia danych pod adresem ${O.email}. Szczegóły na stronie „Dla sklepów”.`,
      ] },
      { h: "9. Postanowienia końcowe", p: [
        "Operator może jednostronnie zmienić regulamin; zmiana wchodzi w życie z chwilą opublikowania jej na tej stronie. Regulamin podlega prawu węgierskiemu; nie narusza to bezwzględnie obowiązujących przepisów o ochronie konsumentów obowiązujących w kraju zamieszkania konsumenta. W razie pytań napisz na podany wyżej adres e-mail.",
      ] },
    ],
    privacy: [
      { p: [`Obowiązuje od: ${U}. Niniejsza polityka wyjaśnia, na podstawie ogólnego rozporządzenia Unii Europejskiej o ochronie danych (RODO, rozporządzenie (UE) 2016/679), w jaki sposób ${S} przetwarza dane odwiedzających.`] },
      { h: "1. Administrator danych", list: operatorLines("pl") },
      { h: "2. W skrócie", list: [
        "W serwisie nie ma rejestracji. O dane osobowe (adres e-mail) prosimy tylko wtedy, gdy zamawiasz powiadomienie o cenie lub dostępności.",
        ADS_ON ? "Nie używamy analitycznych plików cookie. Reklamowe pliki cookie mogą zapisywać wyłącznie reklamy Google i tylko za twoją zgodą (patrz niżej)." : "Nie używamy analitycznych, śledzących ani reklamowych plików cookie.",
        ADS_ON ? "Sami zapisujemy tylko jeden plik cookie: do zapamiętania wybranej waluty." : "Używamy tylko jednego pliku cookie: do zapamiętania wybranej waluty.",
      ] },
      { h: "3. Jakie dane przetwarzamy", list: [
        "Techniczne dane dziennika: przy otwarciu strony serwer dostawcy hostingu (Cloudflare) automatycznie zapisuje adres IP, typ przeglądarki, żądaną stronę i czas. Cel: bezpieczne działanie serwisu, usuwanie błędów, zapobieganie nadużyciom. Podstawa prawna: prawnie uzasadniony interes (art. 6 ust. 1 lit. f RODO). Okres przechowywania: zgodnie z okresem przechowywania dzienników u dostawcy hostingu, najwyżej kilka tygodni.",
        "Plik cookie waluty („cur”): przechowuje walutę wybraną przez użytkownika (np. PLN, EUR) przez 1 rok. Jest niezbędny do działania funkcji, z której korzystasz, i nie zawiera danych osobowych, dlatego nie wymaga zgody.",
        "Linki wychodzące: przycisk „Zobacz w sklepie” przekierowuje do sklepu przez adres /go/…. Nie zapisujemy przy tym danych osobowych. Na stronie sklepu obowiązuje jego własna polityka prywatności.",
        "Kontakt: jeśli napiszesz do nas e-mail, twoje imię i nazwisko, adres e-mail i wiadomość wykorzystamy do udzielenia odpowiedzi i przechowamy je najwyżej 1 rok po zakończeniu sprawy. Podstawa prawna: prawnie uzasadniony interes.",
      ] },
      { h: "Powiadomienia o cenie i dostępności (e-mail)", list: [
        "Jeśli na stronie produktu zamówisz powiadomienie, przetwarzamy: twój adres e-mail, produkt, rodzaj powiadomienia (ponowna dostępność / cena docelowa), cenę docelową i jej walutę, czas złożenia żądania, potwierdzenia i wysyłki oraz jednokierunkowy, skrócony skrót (hash) twojego adresu IP w celu zapobiegania nadużyciom (masowym zapisom).",
        "Cel: wysłanie zamówionego powiadomienia. Podstawa prawna: zgoda (art. 6 ust. 1 lit. a RODO), której udzielasz, klikając link w e-mailu potwierdzającym (podwójne potwierdzenie, double opt-in). Bez potwierdzenia nie wysyłamy żadnych wiadomości.",
        "Zgodę możesz w każdej chwili wycofać za pomocą linku rezygnacji w naszych wiadomościach (dla jednego lub wszystkich powiadomień) albo pod podanym wyżej adresem e-mail.",
        "Okres przechowywania: niepotwierdzone żądania usuwamy automatycznie po 7 dniach, zrealizowane (wysłane) powiadomienia po 30 dniach, a wszystkie pozostałe powiadomienia najpóźniej po 1 roku.",
        "Nie sprzedajemy danych i nie wykorzystujemy ich do reklam ani newsletterów; wysyłamy wyłącznie zamówione powiadomienie. Wiadomości dostarcza wymieniony niżej dostawca usług e-mail.",
      ] },
      ...(ADS_ON ? [{ h: "Reklamy (Google AdSense)", list: [
        "Utrzymanie serwisu wspierają reklamy wyświetlane przez Google AdSense. Nie używamy wyskakujących okienek ani reklam automatycznych; reklamy są oznaczone napisem „Reklama” i pojawiają się na dole list i stron produktów.",
        "W UE okno zgody Google (certyfikowane przez Google, zgodne z IAB TCF) przy pierwszej wizycie pyta, czy zezwalasz na reklamowe pliki cookie i reklamy spersonalizowane. Bez zgody wyświetlane są tylko reklamy niespersonalizowane lub ograniczone. Podstawa prawna: zgoda (art. 6 ust. 1 lit. a RODO); decyzję możesz w każdej chwili zmienić w ustawieniach prywatności na dole strony.",
        "Google może używać plików cookie i identyfikatorów urządzeń do wyświetlania reklam oraz przekazywać dane do USA na podstawie ram ochrony danych UE–USA (EU–US Data Privacy Framework). Szczegóły: policies.google.com/technologies/ads; wyłączenie reklam spersonalizowanych: adssettings.google.com.",
      ] }] : []),
      ...(COFFEE_URL ? [{ h: "Wsparcie („Postaw mi kawę”)", p: [
        `Link na dole strony prowadzi do zewnętrznej strony wsparcia (${coffeeHost}). Wsparcie jest dobrowolne; płatność i potrzebne do niej dane obsługuje ten dostawca zgodnie z własną polityką prywatności. Możemy otrzymać od niego podane przez wspierającego imię i wiadomość.`,
      ] }] : []),
      { h: "4. Podmioty przetwarzające i dostawcy usług", list: hosts("pl") },
      { p: [usNote("pl") + US_BASIS.pl] },
      { h: "5. Twoje prawa", p: [
        "Możesz żądać dostępu do dotyczących cię danych, ich sprostowania, usunięcia lub ograniczenia przetwarzania, a także wnieść sprzeciw wobec przetwarzania opartego na prawnie uzasadnionym interesie. Dane przetwarzane na podstawie twojej zgody (powiadomienia) możesz też otrzymać w formacie nadającym się do odczytu maszynowego (prawo do przenoszenia danych), a zgodę możesz w każdej chwili wycofać. Żądanie wyślij na podany wyżej adres e-mail; odpowiemy w ciągu 30 dni.",
        `Możesz wnieść skargę do Prezesa Urzędu Ochrony Danych Osobowych (UODO, ul. Moniuszki 1A, 00-014 Warszawa, uodo.gov.pl), do węgierskiego organu ochrony danych (${NAIH}) lub zwrócić się do sądu.`,
      ] },
      { h: "6. Zmiany", p: ["Możemy zmieniać niniejszą politykę; aktualna wersja jest zawsze dostępna na tej stronie."] },
    ],
    imprint: [
      { h: "Operator", list: operatorLines("pl") },
      { h: "Dostawcy hostingu", list: hosts("pl") },
      { h: "O serwisie", p: [
        `${S} to niezależna porównywarka cen ASG. Serwis nie jest powiązany z prezentowanymi sklepami ani producentami, chyba że dany link jest częścią programu partnerskiego (patrz Regulamin, pkt 4).`,
      ] },
    ],
    shops: [
      { p: [`${S} raz dziennie zbiera z publicznych stron produktów sklepów nazwę, cenę, walutę, dostępność, markę, kod produktu i adres zdjęcia, a przy każdej ofercie umieszcza link do strony sklepu.`] },
      { h: "Jak zbieramy dane", list: [
        "Nasz robot nazywa się AirsoftHunterBot (szczegóły: /bot).",
        "Przestrzegamy pliku robots.txt, w tym wartości Crawl-delay.",
        "Do każdego sklepu wysyłamy jednocześnie tylko jedno żądanie, w odstępach 2–3 sekund, w nocy.",
        "Odczytujemy wyłącznie publiczne dane produktów zgodne ze schema.org.",
      ] },
      { h: "Poprawki, usunięcie, współpraca", list: [
        `Błędne dane lub prośba o usunięcie: ${O.email}`,
        "Blokada robota: User-agent: AirsoftHunterBot / Disallow: / w pliku robots.txt.",
        "Jeśli oferujesz feed produktowy (XML/CSV) lub program partnerski, chętnie się na niego przełączymy: dane będą dokładniejsze i aktualniejsze, a twój serwer mniej obciążony.",
      ] },
    ],
  };

  // ───────────────────────────── ČESKY ─────────────────────────────
  const cs = {
    terms: [
      { p: [`Platné od: ${U}. Tyto podmínky upravují užívání webu ${S} (${SITE_URL}). Užíváním webu uživatel tyto podmínky přijímá.`] },
      { h: "1. Provozovatel", list: operatorLines("cs") },
      { h: "2. Služba", p: [
        `${S} je bezplatný srovnávač cen a dostupnosti airsoftových produktů, který má pouze informativní charakter. Web není e-shop: neprodává zboží, nepřijímá objednávky a nezpracovává platby.`,
        "Kupní smlouva vzniká výhradně mezi uživatelem a vybraným obchodem, a to za podmínek tohoto obchodu. Web není stranou této smlouvy a neodpovídá za plnění obchodu (doručení, záruka, odstoupení od smlouvy, reklamace).",
      ] },
      { h: "3. Ceny a přesnost údajů", list: [
        "Ceny, informace o dostupnosti a údaje o produktech získáváme automaticky jednou denně z veřejných stránek obchodů, proto se mohou lišit od aktuálních údajů obchodu.",
        "Uvedené ceny nezahrnují poštovné. Ceny obchodů v jiných měnách (např. EUR, HUF) přepočítáváme na zvolenou měnu denním kurzem Maďarské národní banky (MNB); konečná částka v obchodě se může lišit.",
        "Párování produktů probíhá automaticky; může se stát, že se u jednoho produktu zobrazí různé varianty (barva, provedení).",
        "Před nákupem jsou vždy rozhodující údaje na stránce obchodu.",
      ] },
      { h: "4. Odchozí odkazy a partnerské programy", p: [
        "Tlačítko „Zobrazit v obchodě“ vede na stránku obchodu. Některé odkazy mohou být partnerské (affiliate) odkazy: pokud přes ně uživatel nakoupí, může provozovatel získat provizi. Nemá to vliv na cenu, kterou uživatel zaplatí, ani na pořadí výsledků, které se řadí podle ceny, počtu obchodů nebo názvu.",
      ] },
      { h: "5. Upozornění k airsoftovým produktům", list: [
        "Nákup, držení a přeprava airsoftových zbraní se v každé zemi řídí jinými předpisy (např. věkové omezení, limity energie, zákaz zasílání). Za jejich dodržování odpovídá uživatel.",
        "Nezletilí mohou airsoftové zbraně kupovat pouze v souladu s místními předpisy a podmínkami obchodu; mnoho obchodů prodává jen osobám starším 18 let.",
        "Při hře dodržuj místní bezpečnostní pravidla, zejména ochranu očí.",
      ] },
      { h: "6. Duševní vlastnictví", p: [
        "Názvy produktů a značek a loga patří jejich vlastníkům; zobrazují se výhradně za účelem identifikace produktů. Fotografie produktů patří obchodům nebo výrobcům a zobrazují se za účelem prezentace nabídky daného obchodu.",
        "Vlastní obsah webu (design, texty, souhrnná data) není dovoleno bez svolení provozovatele hromadně kopírovat ani získávat automatizovanými nástroji.",
      ] },
      { h: "7. Omezení odpovědnosti", p: [
        "Provozovatel usiluje o nepřetržitý a bezchybný provoz webu, ale nezaručuje ho. V rozsahu, který připouštějí právní předpisy, provozovatel neodpovídá za škody vzniklé použitím údajů z webu, jeho nedostupností nebo ze smluvních vztahů s obchody.",
      ] },
      { h: "8. Obchody a oprávněné osoby", p: [
        `Pokud obchod nechce být na webu uveden nebo zjistí chybné údaje, může požádat o opravu nebo odstranění na adrese ${O.email}. Podrobnosti na stránce „Pro obchody“.`,
      ] },
      { h: "9. Závěrečná ustanovení", p: [
        "Provozovatel je oprávněn tyto podmínky jednostranně změnit; změna nabývá účinnosti zveřejněním na této stránce. Tyto podmínky se řídí maďarským právem; tím nejsou dotčena kogentní ustanovení na ochranu spotřebitele platná v zemi, kde má spotřebitel bydliště. S dotazy se obracej na výše uvedenou e-mailovou adresu.",
      ] },
    ],
    privacy: [
      { p: [`Platné od: ${U}. Tyto zásady popisují na základě obecného nařízení Evropské unie o ochraně osobních údajů (GDPR, nařízení (EU) 2016/679), jak ${S} zpracovává údaje návštěvníků.`] },
      { h: "1. Správce", list: operatorLines("cs") },
      { h: "2. Stručně", list: [
        "Na webu není žádná registrace. Osobní údaje (e-mailovou adresu) požadujeme jen tehdy, když si objednáš upozornění na cenu nebo dostupnost.",
        ADS_ON ? "Nepoužíváme analytické cookies. Reklamní cookies mohou ukládat pouze reklamy Googlu, a to jen s tvým souhlasem (viz níže)." : "Nepoužíváme analytické, sledovací ani reklamní cookies.",
        ADS_ON ? "Sami ukládáme jediný soubor cookie: pro zapamatování zvolené měny." : "Používáme jediný soubor cookie: pro zapamatování zvolené měny.",
      ] },
      { h: "3. Jaké údaje zpracováváme", list: [
        "Technické záznamy (logy): při otevření stránky server poskytovatele hostingu (Cloudflare) automaticky zaznamená IP adresu, typ prohlížeče, požadovanou stránku a čas. Účel: bezpečný provoz webu, hledání chyb, ochrana před zneužitím. Právní základ: oprávněný zájem (čl. 6 odst. 1 písm. f) GDPR). Doba uchování: podle doby uchovávání záznamů u poskytovatele hostingu, nejvýše několik týdnů.",
        "Cookie měny („cur“): ukládá měnu zvolenou uživatelem (např. CZK, EUR) po dobu 1 roku. Je nezbytná pro funkci, kterou používáš, a neobsahuje osobní údaje, proto nevyžaduje souhlas.",
        "Odchozí odkazy: tlačítko „Zobrazit v obchodě“ přesměrovává do obchodu přes adresu /go/…. Přitom nezaznamenáváme žádné osobní údaje. Na stránce obchodu platí jeho vlastní zásady ochrany osobních údajů.",
        "Kontakt: pokud nám napíšeš e-mail, použijeme tvé jméno, e-mailovou adresu a zprávu k vyřízení dotazu a uchováme je nejvýše 1 rok po uzavření věci. Právní základ: oprávněný zájem.",
      ] },
      { h: "Upozornění na cenu a dostupnost (e-mail)", list: [
        "Pokud si na stránce produktu objednáš upozornění, zpracováváme: tvou e-mailovou adresu, produkt, druh upozornění (znovu skladem / cílová cena), cílovou cenu a její měnu, čas žádosti, potvrzení a odeslání a jednosměrný, zkrácený otisk (hash) tvé IP adresy pro ochranu před zneužitím (hromadným přihlašováním).",
        "Účel: odeslání objednaného upozornění. Právní základ: souhlas (čl. 6 odst. 1 písm. a) GDPR), který udělíš kliknutím na odkaz v potvrzovacím e-mailu (dvojí potvrzení, double opt-in). Bez potvrzení nezasíláme žádné e-maily.",
        "Souhlas můžeš kdykoli odvolat odkazem pro odhlášení v našich e-mailech (pro jedno nebo všechna upozornění) nebo na výše uvedené e-mailové adrese.",
        "Doba uchování: nepotvrzené žádosti automaticky mažeme po 7 dnech, splněná (odeslaná) upozornění po 30 dnech a všechna ostatní upozornění nejpozději po 1 roce.",
        "Údaje neprodáváme a nepoužíváme je k reklamě ani k zasílání newsletterů; zasíláme pouze objednané upozornění. E-maily doručuje níže uvedený poskytovatel e-mailových služeb.",
      ] },
      ...(ADS_ON ? [{ h: "Reklama (Google AdSense)", list: [
        "Provoz webu podporují reklamy, které zobrazuje Google AdSense. Nepoužíváme vyskakovací okna ani automatické reklamy; reklamy jsou označeny nápisem „Reklama“ a zobrazují se na konci seznamů a stránek produktů.",
        "V EU se tě okno pro udělení souhlasu od Googlu (certifikované Googlem, podle IAB TCF) při první návštěvě zeptá, zda povoluješ reklamní cookies a personalizované reklamy. Bez souhlasu se zobrazují pouze nepersonalizované nebo omezené reklamy. Právní základ: souhlas (čl. 6 odst. 1 písm. a) GDPR); své rozhodnutí můžeš kdykoli změnit v nastavení ochrany soukromí na konci stránky.",
        "Google může k zobrazování reklam používat cookies a identifikátory zařízení a předávat údaje do USA na základě rámce pro ochranu osobních údajů mezi EU a USA (EU–US Data Privacy Framework). Podrobnosti: policies.google.com/technologies/ads; vypnutí personalizovaných reklam: adssettings.google.com.",
      ] }] : []),
      ...(COFFEE_URL ? [{ h: "Podpora („Kup mi kávu“)", p: [
        `Odkaz na konci stránky vede na externí stránku pro podporu (${coffeeHost}). Podpora je dobrovolná; platbu a údaje k ní potřebné zpracovává tento poskytovatel podle svých vlastních zásad ochrany osobních údajů. Od něj můžeme obdržet jméno a zprávu, které podporovatel uvedl.`,
      ] }] : []),
      { h: "4. Zpracovatelé a poskytovatelé služeb", list: hosts("cs") },
      { p: [usNote("cs") + US_BASIS.cs] },
      { h: "5. Tvoje práva", p: [
        "Můžeš požadovat přístup k osobním údajům, které o tobě zpracováváme, jejich opravu, výmaz nebo omezení zpracování a můžeš vznést námitku proti zpracování založenému na oprávněném zájmu. Údaje zpracovávané na základě tvého souhlasu (upozornění) můžeš na požádání získat i ve strojově čitelném formátu (právo na přenositelnost údajů) a souhlas můžeš kdykoli odvolat. Žádost pošli na výše uvedenou e-mailovou adresu; odpovíme do 30 dnů.",
        `Stížnost můžeš podat u Úřadu pro ochranu osobních údajů (ÚOOÚ, Pplk. Sochora 27, 170 00 Praha 7), u maďarského dozorového úřadu (${NAIH}) nebo se obrátit na soud.`,
      ] },
      { h: "6. Změny", p: ["Tyto zásady můžeme měnit; aktuální znění je vždy k dispozici na této stránce."] },
    ],
    imprint: [
      { h: "Provozovatel", list: operatorLines("cs") },
      { h: "Poskytovatelé hostingu", list: hosts("cs") },
      { h: "O webu", p: [
        `${S} je nezávislý srovnávač cen airsoftu. Web není propojen s uvedenými obchody ani výrobci, s výjimkou případů, kdy je odkaz součástí partnerského programu (viz Podmínky užití, bod 4).`,
      ] },
    ],
    shops: [
      { p: [`${S} jednou denně získává z veřejných stránek produktů jednotlivých obchodů název, cenu, měnu, dostupnost, značku, kód produktu a adresu obrázku a u každé nabídky odkazuje na vlastní stránku obchodu.`] },
      { h: "Jak údaje získáváme", list: [
        "Náš robot se jmenuje AirsoftHunterBot (podrobnosti: /bot).",
        "Dodržujeme soubor robots.txt včetně hodnoty Crawl-delay.",
        "Do každého obchodu posíláme vždy jen jeden požadavek najednou, s pauzami 2–3 sekundy, v noci.",
        "Čteme pouze veřejné údaje o produktech podle schema.org.",
      ] },
      { h: "Oprava, odstranění, spolupráce", list: [
        `Chybné údaje nebo žádost o odstranění: ${O.email}`,
        "Zablokování robota: User-agent: AirsoftHunterBot / Disallow: / v souboru robots.txt.",
        "Pokud nabízíš produktový feed (XML/CSV) nebo partnerský program, rádi na něj přejdeme: údaje budou přesnější a aktuálnější a tvůj server méně zatížený.",
      ] },
    ],
  };

  return { de, pl, cs };
}
