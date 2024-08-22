# JingleBox

A small program that automates playing jingles for sport tournaments.

![Graphical User Interface](https://github.com/jeertmans/jinglebox/assets/27275099/eaa0db1b-4963-419a-9363-b3ce0d687eeb)


## Use case

You are organizing a sport tournament, and games are played every X minutes?

JingleBox can play jingles for every game,
at very precise time moments.
If you are using another software for playing music during the whole event
(e.g., *Spotify*), then it will automatically reduce its volume when jingles
are played.

All the parameters can be modified through the program, and changes will
occur in real time!

## Usage

Depending on your profile, there are two ways to use this application
on your computer.

The requirements are:
- a computer running Windows, Linux, or macOS;
- an application playing music in the background
  (by default, it assumes that you use the *Spotify* desktop application,
  but it can be *Spotify inside your web browser*, videos on *Youtube*, etc.);
- a TOML config file describing **what jingles** should be played and **when**, see
  [`jingles.example.toml`](./jingles.example.toml);
- and, of course, the soundfiles with the audio samples to play for each jingle.

> [!IMPORTANT]
>
> The filepaths (i.e., `file = ...`) to the sound files **must be relative**
> to the location of your configuration file. The easiest way to do so
> is to follow the same structure as this project:
> ```
> .
> ├── jingles.example.toml
> └── jingles
>     ├── 1-next-in-one-minute.mp3
>     ├── 2-time-is-running.mp3
>     ├── 3-halftime.mp3
>     ├── 4-one-minute-left.mp3
>     └── 5-time-is-over.mp3
> ```

### Download the latest executable

If you are a non-programmer, the easiest way to use this application is to download
a pre-built executable. The file is relatively large, but should run the app
without any extra installation from yourself!

Click on the icon corresponding to your OS to download the latest version of JingleBox,
as well as example jingles:

<table>
  <tr>
    <th><a href="https://nightly.link/jeertmans/jinglebox/workflows/build_app/main/jinglebox-macos-latest.zip"><img src="https://github.com/user-attachments/assets/74df860d-cb00-49ab-8953-c254b65556a5" width="64px"></a></th>
    <th><a href="https://nightly.link/jeertmans/jinglebox/workflows/build_app/main/jinglebox-windows-latest.zip"><img src="https://github.com/user-attachments/assets/091c31f9-844b-442d-9ff0-bff0552dde47" width="64px"></a></th>
    <th><a href="https://nightly.link/jeertmans/jinglebox/workflows/build_app/main/jinglebox-ubuntu-latest.zip"><img src="https://github.com/user-attachments/assets/31d80b81-f976-4a38-ab92-568f0c774ecc" width="64px"></a></th>
  </tr>
  <tr>
    <th>macOS</th>
    <th>Windows</th>
    <th>Linux</th>
  </tr>
</table>

### Install locally with Python

This projects requires `Python>=3.10`. After cloning the repository locally,
you can simply install the application with `pip install .`.

Then, you can run the application with: `jinglebox`.

### How it works

The application works with two possible states:

1. *Music*: the music is played at its default level when no jingles are played;
2. *Jingle*: the music level is reduced, and a jingle is played **on top**,
   and the music is put back to its previous level.

Depending on the parameters chosen for the games, such as the duration, the
software will automatically switch between (1) and (2), until the last game is played.

## Help

If you ever need help with this software, please reach me using the GitHub
issues, or via my email:
[jeertmans@icloud.com](mailto:jeertmans@icloud.com).
