# pyt semestral project

TODO: translate to english


Interní aplikace pro naší firmu určená pro správu firemních bodů. Body
udělují project manažeři, nebo admin (=> uživatelské role). Za body lze
koupit několik odměn. Aplikace by byla webová - backend v pythonu a
frontend pomocí flasku (nebo JS?). Frontendy budou prakticky dva. Jeden
pouze pro obecný přehled (pořadí, ceny, ...), který poběží na televizi.
Druhý frontend bude pro uživatele, kde budou zpřístupněné jednotlivé
funkce podle role uživatele. Aplikace bude dále propojená se systémy
JIRA (nástroj pro project management, kde má uživatel tasky) a toggl
(time tracking).

Funkční požadavky:
- login pomocí firemního gmailu
- admin a PM mají možnost přidělit body (s oduvodněním)
- přehled možných cen a vlastních bodů
- přehled, za co lze body získat
- možnost vyzvednout jednu z cen
- přehled vlastních tasků z jiry
- možnost spustit / zastavit timer na tasku v togglu
- možnost měnit status tasku z jiry
- možnost přidat komentář k tasku z jiry

Nefunkční požadavky:
- uživatelské role
- podpora mobilních zařízení (PWA?)
- testy
- dokumentace pomocí Sphinx
- obecné řešení jako open source
