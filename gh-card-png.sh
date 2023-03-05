#!/bin/bash

read -p 'User: ' user
repo='Placeholder'

while [ "$repo" ]
do
    read -p 'Repo: ' repo
    wget "https://gh-card.dev/repos/$user/$repo.svg"
    inkscape "$repo.svg" --export-type=png -h 540 -o "$repo.png"

done
