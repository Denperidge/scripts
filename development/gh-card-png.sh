#!/usr/bin/env bash

# Leverages the gh-card project to create PNG repo cards
# Because some document formats doesn't support SVG's.
#
# Requirements: bash, wget, inkscape
# External endpoints: https://gh-card.dev/
# Last update: < 5 March 2023

read -p 'User: ' user
repo='Placeholder'

while [ "$repo" ]
do
    read -p 'Repo: ' repo
    wget "https://gh-card.dev/repos/$user/$repo.svg"
    inkscape "$repo.svg" --export-type=png -h 540 -o "$repo.png"
done
