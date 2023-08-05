# JingleBox

A small program that automates playing jingles for sport tournaments.

## Use case

You are organizing a sport tournament, and games are played every X minutes?

JingleBox can play jingles (defined in `jingles.toml`) for every game,
at very precise time moments.
If you are using another software for playing music during the whole event
(e.g., Spotify), then it will automatically reduce its volume when jingles
are played.

All the parameters can be modified through the program, and changes will
occur in real time!

## How to use

This software requires `Python>3.8` and to be on a Linux distro
(at least for reducing the volume of, e.g., Spotify). You will also
need to clone or copy this repository, and install Poetry.

You can install this package and its dependencies with: `poetry install`.

And you can run the GUI with: `poetry run python -m jinglebox`.

## Help

If you ever need help with this package, please reach me using the GitHub
issues, or via my email:
[jeertmans@icloud.com](mailto:jeertmans@icloud.com).
