# Démarche de réalisation du projet — B1 à B5

## Objet du document

Ce document présente la progression suivie pour construire l’application du
Festival du Rire de Deauville, du premier affichage de données en B1 jusqu’au
package Python, à l’API d’administration et aux tests du contrat en B5. Il
explique les objectifs de chaque étape, les choix d’organisation du code et la
manière dont les règles du festival ont été progressivement déplacées vers
une conception plus fiable.

Le projet utilise les données de `data/festival.json` comme jeu de départ. Les
versions successives ont été conservées séparément afin de pouvoir comparer
les notions apprises sans écraser le travail des étapes précédentes.

## Vue d’ensemble de la progression

| Bloc | Question traitée | Résultat principal |
| --- | --- | --- |
| B1 | Comment lire et explorer des données JSON ? | Un premier programme procédural dans `main.py`. |
| B2 | Comment organiser les opérations et faire respecter les règles ? | Un programme en fonctions, avec dates, erreurs et sauvegarde, dans `main_b2.py`. |
| B3 | Comment réutiliser les règles entre le terminal et un site web ? | Des objets métier, une API FastAPI et des tests dans les fichiers `*_b3.py`. |
| B4 | Comment représenter plusieurs types de spectacles et empêcher les modifications non contrôlées ? | Un package orienté objet, polymorphe, avec administration et stockage interchangeable dans `src/deauville/`. |
| B5 | Comment prouver que l’API respecte son contrat et livrer le projet ? | Des tests HTTP isolés, une documentation d’utilisation et un package construit avec `uv build`. |

## B1 — Explorer le JSON et produire un programme simple

### Point de départ

Le fichier `data/festival.json` contient un objet JSON avec les informations du
festival, ses lieux, ses artistes et ses spectacles. En Python, le module
`json` transforme ce document en dictionnaires et listes. Le programme peut
alors accéder aux champs, par exemple à la liste des lieux ou au titre d’un
spectacle.

### Construction

Dans [main.py](./main.py), le travail reste volontairement procédural :

1. ouvrir le fichier JSON en UTF-8 et le charger avec `json.load` ;
2. lire les informations principales et afficher le nom, les dates et les
   nombres d’éléments ;
3. parcourir les listes avec `for` et filtrer les spectacles avec `if` ;
4. utiliser des accumulateurs et des dictionnaires pour calculer des totaux,
   compter les types de spectacles et repérer les artistes les plus présents ;
5. demander une date au clavier et répéter la demande avec `while` tant que la
   valeur n’est pas une date proposée par les données ;
6. afficher les spectacles correspondant à la date choisie.

Cette première version permet de raisonner directement sur les données. En
revanche, les informations de date restent du texte et les règles sont
dispersées dans le déroulement du programme.

### Limite conservée pour illustrer l’étape

Dans B1, le programme associe un spectacle à la date civile écrite au début de
son horaire. Un spectacle commençant après minuit n’est donc pas encore
rattaché à la journée de festival qui a commencé la veille. Cette limite est
signalée dans le README principal et sert de point de comparaison avec le
traitement des vraies dates introduit en B2.

## B2 — Factoriser, gérer les horaires et enregistrer les changements

### Passer des instructions aux fonctions

La deuxième version est dans [main_b2.py](./main_b2.py), sans remplacer
`main.py`. Les traitements réutilisables sont isolés dans des fonctions :

- `load_festival` et `save_festival` pour les fichiers ;
- `find_venue` et `find_artist` pour retrouver les éléments par identifiant ;
- des fonctions de calcul et de formatage pour les débuts, fins et journées de
  festival ;
- des fonctions d’affichage pour le résumé, le programme, un artiste et les
  spectacles en cours ou à venir ;
- des fonctions pour ajouter et annuler un spectacle.

Le point d’entrée analyse les arguments de la ligne de commande et choisit le
traitement correspondant. Les calculs renvoient des valeurs lorsqu’ils doivent
être réutilisés ; l’affichage reste dans les fonctions responsables de
l’interface terminal.

### Dates et règle de la journée de festival

Les horaires sont désormais convertis en objets `datetime` et les dates de
festival en objets `date`. Une durée est représentée par `timedelta`. La fin
d’un spectacle se calcule à partir de son début et de sa durée.

La journée de festival commence à 06 h : on soustrait six heures à l’heure de
début avant de prendre la date. Ainsi, un spectacle qui commence le 12 juin à
01 h appartient à la journée de festival du 11 juin. Cette règle permet de
corriger la limite de B1, de trier les spectacles et de savoir quels spectacles
sont en cours à un instant donné.

### Contrôle des erreurs, règles et sauvegarde

Avant d’ajouter un spectacle, le programme vérifie notamment que :

- la date appartient à la durée du festival ;
- le lieu et les artistes existent ;
- la durée respecte les limites prévues ;
- le lieu n’est pas déjà réservé sur un horaire incompatible ;
- un artiste n’est pas engagé dans un autre spectacle, quel que soit son rôle ;
- un délai de 30 minutes est respecté entre deux réservations concernées.

Une règle non respectée provoque une erreur explicite. Le point d’entrée
intercepte les erreurs attendues et affiche un message plutôt qu’une trace
technique. Les commandes d’ajout et d’annulation sauvegardent leurs changements
en JSON.

### Préserver les versions et les données d’origine

B2 enregistre les modifications dans `data/festival_b2.json`. La lecture peut
partir du fichier initial, mais les opérations d’écriture ciblent le fichier
B2. Le fichier de référence `data/festival.json` n’est donc pas le fichier
modifié par ces commandes.

## B3 — Créer un modèle métier réutilisé par l’API et le terminal

### Pourquoi introduire des classes ?

En B2, les données restent principalement des dictionnaires. Les classes de
B3 regroupent les données et les comportements qui vont ensemble. La version
est conservée dans [festival_b3.py](./festival_b3.py) ; elle ne remplace pas
`main_b2.py`.

Le modèle représente notamment :

- `Venue` et `Artist`, avec leurs identifiants lisibles sous forme de slugs ;
- `Performance`, avec les calculs communs d’heure de fin, de journée de
  festival, d’identifiant, de tri et de représentation ;
- `Festival`, qui rassemble les lieux, artistes et spectacles et devient le
  point d’accès aux règles de planning.

Le modèle sait produire des vues destinées à l’API et des données destinées à
la sauvegarde. Les méthodes du festival donnent accès au programme d’une
journée, aux spectacles d’un artiste, à ceux qui sont en cours et aux suivants.

### Deux interfaces sur un même domaine

- [main_b3.py](./main_b3.py) fournit une interface en ligne de commande.
- [api_b3.py](./api_b3.py) expose les informations avec FastAPI et sert les
  pages publiques de `web/public/`.

Les deux interfaces s’appuient sur le modèle `Festival` : la validation du
planning ne dépend donc plus exclusivement de la commande terminal ou d’une
route HTTP. L’API fournit notamment les informations du festival, des lieux,
des artistes, du programme, d’un spectacle et des spectacles en cours ou à
venir.

Les écritures B3 utilisent `data/festival_b3.json`. Comme pour B2, la version
précédente et le fichier de départ sont préservés.

### Tester les règles

`tests/test_b3.py` vérifie le calcul de la journée après minuit, les durées,
les conflits de lieu et d’artistes, les références inconnues, l’annulation,
les spectacles en cours et à venir, les réponses API et la sauvegarde dans un
fichier distinct. Les tests construisent un festival contrôlé au lieu de
dépendre d’un serveur lancé manuellement.

## B4 — Généraliser les spectacles et protéger l’état du festival

### Une famille de types de spectacles

Le modèle B4/B5 se trouve dans
[src/deauville/festival.py](./src/deauville/festival.py). La classe abstraite
`Performance` porte les éléments communs : titre, lieu, début, durée, fin,
journée de festival et identifiant. Elle impose aussi aux sous-classes de
fournir leur type, leurs artistes, leur résumé et leurs champs spécifiques.

Trois sous-classes décrivent les comportements particuliers :

- `SoloShow` représente un spectacle individuel et valide l’âge minimum ;
- `Lineup` représente un plateau avec un animateur et plusieurs artistes ; il
  vérifie le nombre d’artistes, les doublons, le rôle de l’animateur et la
  durée minimale ;
- `Workshop` représente un atelier avec un enseignant et des participants ;
  ses places sont limitées à la fois par le maximum demandé et par la capacité
  du lieu.

Le code peut demander à chaque objet son résumé ou ses artistes sans devoir
répéter partout une série de conditions sur son type. Le type du spectacle est
utilisé au chargement des données pour construire la bonne sous-classe.

### Encapsulation et règles centralisées

`Festival` possède l’état du festival. Ses collections sont exposées comme
des tuples en lecture seule ; les listes d’artistes d’un plateau et les
participants d’un atelier sont également protégés contre les modifications
directes depuis l’extérieur.

Les changements passent par des méthodes du domaine comme `add`, `replace`,
`cancel`, `register_participant` et `add_artist`. Elles valident les données
et les conflits avant la sauvegarde. Un déplacement refusé conserve ainsi le
planning initial. Si une sauvegarde échoue après une modification, l’état
mémoire est restauré plutôt que de laisser croire que l’opération a réussi.

Les erreurs métier sont séparées dans
[src/deauville/errors.py](./src/deauville/errors.py) : ressource introuvable,
conflit et valeur invalide. Cette distinction permet à l’API de retourner des
codes HTTP adaptés, sans placer les règles dans les routes.

### Stockage interchangeable et interface d’administration

[src/deauville/storage.py](./src/deauville/storage.py) définit le contrat
`FestivalStorage` et deux solutions :

- `JsonStorage` lit et écrit un fichier JSON ;
- `MemoryStorage` conserve une copie en mémoire, principalement utile pour les
  tests isolés.

Le modèle dépend de cette interface plutôt que d’un fichier concret. Les
règles métier peuvent donc être conservées si une autre solution de stockage
est ajoutée plus tard.

L’API dans [src/deauville/api.py](./src/deauville/api.py) ajoute les
opérations d’administration : création, modification et suppression de
spectacles, inscription à un atelier et ajout d’artistes. Pydantic valide la
forme des requêtes, puis les opérations métier du festival valident les règles
du domaine. Les pages publiques et d’administration sont dans `web/public/`
et `web/admin/`.

## B5 — Tester le contrat et préparer la livraison

### Une application créée pour chaque contexte

`create_app(storage)` construit l’application autour d’un stockage fourni.
L’exécution normale utilise le stockage JSON ; les tests utilisent un stockage
en mémoire ou des fichiers temporaires. Cette factory évite que les tests se
partagent un état global et empêche les essais de modifier les données de
départ.

Les tests de [tests/test_b5.py](./tests/test_b5.py) couvrent les routes et les
comportements HTTP, notamment :

- les routes de lecture et leurs filtres ;
- les ressources inconnues et les statuts d’erreur ;
- la validation des requêtes ;
- la création, la modification et la suppression ;
- les inscriptions aux ateliers et la gestion des doublons ;
- les collisions de slugs d’artistes ;
- l’échec de sauvegarde et le retour à l’état précédent ;
- l’absence de modification du JSON initial ;
- le premier chargement d’un chemin de données personnalisé qui n’existe pas
  encore.

Les tests d’ensemble couvrent les règles métier B3/B4 et l’API B4/B5. La
vérification effectuée à la finalisation donne **66 tests réussis** avec
`uv run pytest -q`.

### Packaging et qualité

Le point d’entrée installable `deauville` est configuré dans
[pyproject.toml](./pyproject.toml). Le package est construit à partir du
dossier `src/` avec Hatchling ; les ressources web et le JSON de départ sont
inclus dans la distribution.

Les contrôles de livraison utilisés sont :

```powershell
uv sync
uv run ruff check .
uv run pytest -q
uv build
```

La commande de développement démarre l’application ainsi :

```powershell
uv run deauville
uv run deauville programme 2027-06-11
uv run deauville serve
```

Le serveur expose les pages publiques à `/`, l’administration à `/admin/` et
la documentation interactive de FastAPI à `/docs`. Le fichier d’écriture par
défaut est `data/festival_b4.json` ; `data/festival.json` reste la source
initiale et n’est pas écrasé. L’option `--data` permet de choisir un autre
fichier de travail.

## Exemple de parcours d’une requête d’administration

Pour expliquer le lien entre l’API et les règles métier à l’oral, on peut
suivre une création de spectacle :

1. le client envoie un `POST /api/performances` avec un corps JSON ;
2. le modèle Pydantic `PerformanceInput` vérifie la structure des champs ;
3. `Festival.performance_from_input` construit l’objet adapté au type demandé ;
4. `Festival.add` contrôle les références, les limites et les conflits ;
5. le festival sauvegarde le nouvel état au moyen du stockage fourni ;
6. l’API transforme une erreur métier en réponse HTTP appropriée, ou renvoie
   le spectacle créé si toutes les vérifications réussissent.

Ce parcours illustre la séparation recherchée : la route reçoit et traduit la
requête, le domaine décide si l’opération est permise et le stockage se charge
de la persistance.

## Organisation finale des principales versions

```text
main.py                 Version procédurale B1
main_b2.py              Version en fonctions B2
festival_b3.py          Modèle objet B3
main_b3.py              Interface terminal B3
api_b3.py               API et pages publiques B3
src/deauville/          Package commun B4/B5
web/public/             Pages publiques
web/admin/              Interface d’administration
data/festival.json      Données initiales
tests/test_b3.py        Tests du modèle/API B3
tests/test_b4.py        Tests d’héritage, règles et administration
tests/test_b5.py        Tests du contrat HTTP et de l’isolation
```

Cette organisation conserve les étapes pédagogiques tout en faisant du
package `deauville` la version finale à exécuter et à livrer.

## Périmètre et limites connues

- Les documents de cours mentionnent un fichier `API.md` distinct, mais ce
  fichier n’est pas fourni dans le dépôt. Les routes et tests ont donc été
  construits à partir des fiches disponibles et des comportements réellement
  implémentés.
- Le stockage JSON et le stockage en mémoire sont disponibles. Le stockage
  SQLite évoqué comme extension n’a pas été réalisé.
- Le comportement B1 après minuit est conservé comme limite de cette première
  étape ; les versions B2 à B5 appliquent la règle des six heures.
- Le serveur utilise le port `8000` par défaut. Si ce port est déjà utilisé,
  il faut lancer le serveur sur un autre port disponible plutôt que d’arrêter
  un processus qui ne fait pas partie du projet.
