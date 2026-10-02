# L’expérience humaine

Site statique de présentation du roman, généré depuis `presentation.md`. Le site fonctionne sans JavaScript et s’adapte aux écrans mobiles.

## Installation

Créer l’environnement Python, l’activer et installer les dépendances :

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --require-hashes -r requirements.txt
```

## Génération

```bash
./gen.sh
```

La commande produit dans `web/` :

- `index.html`, généré depuis `presentation.md` et `template.html` ;
- `social-card.png`, image utilisée par les métadonnées de partage ;
- `experience-humaine.pdf`, version A4 composée directement depuis la présentation.

Les générateurs Python se trouvent dans `script/`. Toute modification du contenu passe par `presentation.md`, puis par `./gen.sh`.

## Structure de la présentation

Le titre de niveau 1 et le champ `Auteur` alimentent l’en-tête et les métadonnées. Pour un titre de section contenant deux-points, seule la partie située après les deux-points est affichée. Un titre sans deux-points structure le document sans apparaître dans la page.

Dans le bouton de la section `Action`, `**texte**` produit du gras et la séquence `\n` force un saut de ligne.

## Serveur local

```bash
./web.sh
```

Le site est disponible à l’adresse [http://localhost:8000](http://localhost:8000).

## Publication

Une poussée sur la branche `main` déclenche le workflow GitHub Pages. Celui-ci installe les dépendances, exécute `./gen.sh` et publie le dossier `web/`.
