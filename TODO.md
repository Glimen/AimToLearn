# TODO

Idées évoquées pendant le développement et pas encore traitées.

## Jeu

- [ ] **Mode "gamer"** : mode de perfectionnement pour joueurs à l'aise, avec des skins
  pour le rendre plus ludique. Les couleurs sont déjà regroupées dans `COLORS`
  (`config/settings.py`), point de départ pour les skins.
- [ ] **Calibrer la difficulté avec de vrais joueurs débutants** (le bot de test joue trop bien) :
  - vitesse de référence `REFERENCE_THROUGHPUT` (3 bits/s = 100 %) ;
  - poids des scores (40 % précision / 30 % complétion / 30 % vitesse) ;
  - seuil de passage (plus de 70 %) ;
  - tailles, vitesses et durées de vie des cibles (`config/levels.py`).
- [ ] **Écran de consigne**, options proposées mais non retenues pour l'instant :
  - bouton "Commencer" au lieu de "clique n'importe où" (évite de lancer le niveau par erreur) ;
  - aperçu de la cible et du nombre de cibles ;
  - rappel des règles de score.

## Version web (pygbag)

- [ ] Vérifier dans le navigateur, sur https://glimen.github.io/AimToLearn/ :
  - le son (si le mixer web n'est pas en 16 bits, le jeu passe en silencieux :
    prévoir alors des fichiers `.ogg`) ;
  - la conservation des scores (localStorage) après rechargement de la page ;
  - la saisie du nom : accents et clavier AZERTY.

## Distribution

- [ ] Avertissement SmartScreen sur l'exe non signé : signature de code (certificat payant)
  ou procédure illustrée "Informations complémentaires > Exécuter quand même" pour les joueurs.
- [ ] Si des antivirus signalent l'exe : passer PyInstaller en mode dossier (`--onedir`)
  au lieu de `--onefile`.
- [ ] Builds macOS et Linux via GitHub Actions (à construire sur chaque système).

## Maintenance

- [ ] Token GitHub utilisé par Claude : expire le 25/12/2026. Le révoquer ou le renouveler
  avec une expiration plus courte.
