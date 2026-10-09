Testovací oprava inicializace SKT editoru

- Odstraněn watchdog, který mohl po prodlevě obnovit celou stránku, ale neověřoval funkčnost kliknutí.
- Načtení core/tableEditor.js přesunuto až za registraci inicializace FancyTable, aby se editor připojoval až po skriptech tabulky.
- Samotný tableEditor.js zůstává beze změn.

Jde o cílenou testovací změnu pořadí inicializace. Ověř ji ve Firefoxu v oEmbedu po běžném načtení i po F5. Původní soubory si ponech jako zálohu.
