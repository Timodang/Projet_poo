# PythonPOO

## Description des fonctionnalités du projet

L'objectif de ce projet est de construire un framework d'analyse de portefeuille. Le projet est organisé autour de plusieurs classes :
- data_formating : classe utilitaire permettant de nettoyer des données importées.
- data_loader : classe permettant d'importer et de convertir en dataframe des tableaux de données contenant les NAV des fonds que l'utilisateur souhaite ajouter à son portefeuille et les séries de facteurs d'AQR utilisées pour réaliser une analyse factorielle.
- descriptive_stats : classe permettant de calculer un ensemble de statistiques descriptives (perf, vol, ...).
- factor_analysis : classe permettant de réaliser une analyse factorielle.
- portfolio : classe permettant de construire un portefeuille et d'effectuer les calculs / de renvoyer les métriques sur les fonds utilisés.
- visualisation : classe permettant de réaliser des graphiques / tableaux pour synthétiser l'analyse.

Les principaux fichiers de ce projet sont : 
- La main
- Le projet de test unitaire
- L'application streamlit

Dans le cas où l'utilisateur lance la main, il va construire son portefeuille. Par défaut, le programme prévoit l'ajout de 4 fonds. L'arboresecence des fichiers
s'ouvre pour permettre à l'utilisateur de sélectionner les fichiers (excel / csv) contenant les NAV de chaque fonds qu'il souhaite importer. 

Le projet de test unitaire s'appuie sur un fichier excel fourni dans le répertoire test. Ce dernier contient l'essentiel des calculs réalisés directement dans un excel
retraité afin de comparer les résultats avec ceux du code.

## Points d'amélioration

Nous avons un bug sur le streamlit concernant l'affichage des graphiques de performance cumulé. Nous ne sommes pas parvenus à débogguer et affichons donc le graphique depuis la main plutôt que depuis l'application. 

Pour aller plus loin dans le développement du code, il faudrait donner à l'utilisateur la possibilité de sélectionner l'univers d'investissement pour les séries d'AQR pour chaque
fonds importé. L'implémentation actuelle importe les fichiers une seule fois et récupère directement les séries pour un univers d'investissement donné ('global' dans la main). 

Nous avons eu des difficultés avec la gestion des dates sur les graphiques streamlit. Les dates en abcisse ne sont pas exhaustives.

## Remarques

L'exécution du code prend un certain temps (entre 3 et 5 minutes pour avoir des résultats). Ce temps d'exécution provient de l'import des séries quotidiennes de facteurs d'AQR. 

La visualisation des données n'est pas implémentée dans la main. Elle est uniquement implémentée à travers l'application streamlit.

Trois tests unitaires sont rejetés à une précision de 4 chiffres après la virgule. Il s'agit des tests liés au calcul du rendement
excédentaire annualisé. Il existe en effet un décalage à partir de la troisième décimale entre les valeurs de l'excel et les résultats du code. Malgré ce décalage, les valeurs attendues restent très proches des valeurs obtenues (test validé pour une précision de deux décimales).

