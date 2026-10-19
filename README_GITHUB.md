# 🎭 Festival du Rire de Deauville

**Application de gestion d'un festival de spectacles**, développée progressivement en Python, d'un script de consultation JSON à une application structurée avec API REST, interface web et tests automatisés.

## 📌 Présentation

Ce projet permet de consulter et d'administrer la programmation du Festival du Rire de Deauville : lieux, artistes, spectacles et ateliers. Il illustre l'évolution d'une application au fil de cinq blocs pédagogiques (**B1 à B5**), tout en conservant chaque version pour suivre les améliorations.

## ✨ Fonctionnalités

- Consultation des informations du festival, des lieux et des artistes.
- Affichage du programme par journée et des spectacles en cours ou à venir.
- Ajout, modification et annulation de spectacles.
- Inscription de participants aux ateliers et ajout d'artistes.
- Vérification des contraintes de planning : disponibilités, conflits, durées et délais entre réservations.
- Sauvegarde des données en JSON et stockage en mémoire pour les tests.
- Accès via terminal, API REST et interfaces web publique et d'administration.

> **Règle métier importante :** une journée de festival commence à **06 h**. Un spectacle à 01 h est donc rattaché à la journée précédente (à partir de B2).

## 🛠️ Technologies

- **Python** — logique métier et interface en ligne de commande
- **FastAPI** — API HTTP
- **Pydantic** — validation des requêtes
- **JSON** — données et persistance
- **Pytest** — tests automatisés
- **Ruff** — vérification du code
- **uv / Hatchling** — environnement et packaging

## 🚀 Installation et démarrage

### Prérequis

- Python compatible avec le projet
- [uv](https://docs.astral.sh/uv/) installé

### Installer les dépendances

```bash
uv sync
```

### Lancer l'application

```bash
# Afficher les informations générales
uv run deauville

# Consulter le programme d'une journée
uv run deauville programme 2027-06-11

# Démarrer le serveur web
uv run deauville serve
```

Une fois le serveur démarré, les interfaces sont accessibles aux adresses suivantes :

| Espace | Adresse |
| --- | --- |
| Site public | `http://localhost:8000/` |
| Administration | `http://localhost:8000/admin/` |
| Documentation interactive de l'API | `http://localhost:8000/docs` |

Le port par défaut est **8000**.

## 🧱 Évolution du projet

| Bloc | Objectif | Réalisation |
| --- | --- | --- |
| **B1** | Découvrir les données | Lecture JSON, boucles, filtres et affichage du programme |
| **B2** | Structurer le code | Fonctions, gestion des dates, validation et sauvegarde |
| **B3** | Réutiliser la logique métier | Classes Python, interface CLI, API FastAPI et premiers tests |
| **B4** | Renforcer l'architecture | Héritage, polymorphisme, encapsulation, administration et stockage interchangeable |
| **B5** | Fiabiliser et livrer | Tests HTTP isolés, création d'application configurable et packaging |

### Architecture métier

La version finale distingue trois responsabilités :

1. **API / interfaces** : réception des demandes et présentation des résultats.
2. **Domaine (`Festival`)** : application des règles de gestion et validation du planning.
3. **Stockage (`FestivalStorage`)** : lecture et écriture des données, en JSON ou en mémoire.

Les spectacles sont représentés par une classe abstraite `Performance` et trois types spécialisés : `SoloShow`, `Lineup` et `Workshop`.

## 📂 Structure du projet

```text
.
├── main.py                 # B1 : version procédurale
├── main_b2.py              # B2 : version fonctionnelle
├── festival_b3.py          # B3 : modèle métier
├── main_b3.py              # B3 : interface terminal
├── api_b3.py               # B3 : API
├── src/deauville/          # B4/B5 : package final
│   ├── festival.py         # Modèles et règles métier
│   ├── api.py              # Routes HTTP
│   ├── storage.py          # Abstraction du stockage
│   └── errors.py           # Erreurs métier
├── web/
│   ├── public/             # Site public
│   └── admin/              # Administration
├── data/
│   └── festival.json       # Données d'origine
├── tests/                  # Tests automatisés
└── pyproject.toml          # Configuration du projet
```

## 🧪 Tests et qualité

Pour exécuter les vérifications :

```bash
uv run ruff check .
uv run pytest -q
uv build
```

La validation documentée lors de la finalisation du projet indique **66 tests réussis**. Les tests couvrent notamment les règles de programmation, les réponses HTTP, les conflits, les erreurs de sauvegarde et la préservation des données initiales.

## 💾 Gestion des données

Le fichier `data/festival.json` sert de **jeu de données initial** et n'est pas écrasé par les opérations de la version finale. Le fichier de travail par défaut est `data/festival_b4.json` ; l'option `--data` permet d'utiliser un autre chemin.

## 📈 Points techniques abordés

Ce projet met en pratique la programmation procédurale et fonctionnelle, la programmation orientée objet, l'héritage et le polymorphisme, la séparation des responsabilités, la conception d'API REST, les tests automatisés et le packaging Python.

## 🔎 Limites actuelles

- Stockage disponible en **JSON** ou **en mémoire** ; pas d'implémentation SQLite.
- La première version B1 ne gère pas encore le rattachement après minuit, corrigé dès B2.
- La documentation des routes est accessible via l'interface FastAPI `/docs`.

---

**Projet pédagogique Python — Festival du Rire de Deauville (B1 → B5).**
