# Bambam Plus 
## TUI Easy Configuration ✓
## New Extensions Support ✓
## Future Educational Mode

### New in this Fork
- **TUI Launcher** (`bambam_tui.py`): Curses-based menu for configuration and launching
- **Configuration System** (`bambam_config.py`): Persistent YAML settings
- **Cage Support**: Run in kiosk mode via cage compositor
- **Background Images**: Custom background image support
- **Auto-Switch**: Random mode/background changes based on keypress count
- **All-Modes Button**: Run through all extensions
- **Pi 5 Lite Guide**: Complete Raspberry Pi deployment documentation

[![Build Status](https://github.com/porridge/bambam/actions/workflows/python-app.yml/badge.svg)](https://github.com/porridge/bambam/actions/workflows/python-app.yml)
[![Translation Status](https://hosted.weblate.org/widgets/bambam/-/app-and-manpage/svg-badge.svg)](https://hosted.weblate.org/engage/bambam/)

# Fork goals/phases
  Stage 1) Make simple animal sounds, instruments, drums, vehicles, and "silly stuff" (random fart noises and such) extensions
  Stage 2) Default "bambam" terminal keybind that opens with cage - swaylock option so even if your baby types quit somehow (they will) youre good
  Stage 3) Integrate more educational extensions with a similar style, i would not recommend this app to kids above 1.5-2 years old

## (Future) educational edition 
Children learn in a much different way than us adults, simple word-sight-sound associations are extremely effective for word development, phonetics and critical thinking skills.
Shows like cocomelon, baby shark, etc do not provide the direct association young toddlers/kids need to increase their linguistic skills. This of course begs the question,
how does randomly compiled crap like this do better? The way kids learn language is extremely less constrained due to a lack of understanding, does your 2 year old 
know please means to graciously ask someone for something or do they know "peez=fruit pouch". My philosophy with this late stage addition is to take advantage of their
norepinephrine + dopamine seeking behaviors that are intrinsic to modern day life regardles of circumstance. The keyboard mashing registers as a dopamine hit yet 
subconsciously functions like a classic picture book (blue light filtering and low brightness optimization will be immediate in stage 1). the truth is, 
if your child sees you using technology theyre gonna want in. But they cannot tell the difference between engineered useless dopamine hits vs learning with a dopamine appetizer

## Psychology documentation references 

https://www.tandfonline.com/doi/full/10.1080/15475441.2019.1670184

-note this next one is stupid because some moron thinks white kid brains are different. they're not and that person is stupid (still interesting)
https://www.nature.com/articles/s41598-023-34049-3

https://pmc.ncbi.nlm.nih.gov/articles/PMC6335198/

## ORIGINAL DOCS START vvvvv
 
Bambam is a simple baby keyboard (and gamepad) masher application that locks the keyboard and mouse and instead displays bright colors, pictures, and sounds.  While OSX has great programs like [AlphaBaby](http://www.kldickey.addr.com/alphababy/), the original author couldn't find anything for Linux and having wanted to learn Python for a while, Bambam was his excuse.

![Bambam screenshot](docs/bambam.png "Bambam screenshot")
## Installation

### From a distribution package

First, see if your distribution has a bambam package already.
This way takes care of dependencies, translated program messages, `.desktop` files and manual pages.

For example:
```
sudo apt install bambam
man bambam
```

### Manual installation

If not, you can install it manually as follows.

Before installing this application, ensure you have the following installed:
  * [Python](http://python.org) - versions 3.9, 3.11 and 3.13 are supported
  * [Pygame](http://www.pygame.org/) - version 2.x is supported, but version 1.9 might work too. See [install instructions](https://www.pygame.org/wiki/GettingStarted).
  * [PyYAML](https://github.com/yaml/pyyaml) - only required for using
    [extensions](#extensions); any reasonably recent version should work

Then:
  1. [Download](https://github.com/porridge/bambam/releases) the `bambam-1.4.1.zip` or `bambam-1.4.1.tar.gz` file.
  1. Unzip `bambam-1.4.1.zip` or `tar zxvf bambam-1.4.1.tar.gz` to create the `bambam-1.4.1` directory.
  1. Change into the `bambam-1.4.1` directory
```
cd bambam-1.4.1
```

Then you can read the documentation with:
```
man ./bambam.6
```

If you would like to take advantage of the recommended way to start the game (see the next section) do the following:

```
sed -i -e "s,/usr/games/bambam,`pwd`/bambam.py," bambam-session.desktop
sudo mkdir -p /etc/X11/sessions
sudo cp bambam-session.desktop /etc/X11/sessions/
```

For an alternative way to start the game from your applications menu, do the following:
```
sed -i -e "s,/usr/games/bambam,`pwd`/bambam.py," bambam.desktop
mkdir -p ~/.local/share/applications
cp bambam.desktop ~/.local/share/applications/
```

## Quick Start (TUI Launcher)

The easiest way to configure and run BamBam Plus:

```bash
# Interactive TUI menu
./bambam_tui.py

# Run with saved configuration
./bambam_tui.py --run

# Run in cage compositor (kiosk mode)
./bambam_tui.py --run-cage
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for comprehensive documentation and [PI5_DEPLOYMENT.md](PI5_DEPLOYMENT.md) for Raspberry Pi setup.

## Usage

Once installed, there are two ways to run the game:
1. **Recommended**: as a dedicated graphical session.

   When logging into your system, look for a gear icon, which opens a drop-down
   menu of available session types. Select BamBam and log in.

   This way only the game is launched, and the user is logged out as soon as
   the game quits.  Thanks to this, a child is not able to cause any damage
   even if he or she somehow manages to quit the game.

   This way is safer, but more cumbersome.
2. **Alternative**: Directly from a terminal, or applications menu.

   Select the game from your applications menu, or to run the game from a
   terminal window, type `bambam` if you installed from a distribution package, or
   `./bambam.py` if you installed manually.

   **Why this way is not recommended:**

   This way the program runs as part of a regular session. The game tries to
   grab the keyboard and mouse pointer focus in order to prevent a child from
   exiting the game or switching away from it. However it is not 100%
   bulletproof, depending on the exact environment.

   This way is easier, but potentially more risky. Take care when leaving your
   child unattended with the game.

## Exiting

To exit, just directly type the command mentioned in the upper left-hand corner of the window. In the English locales, this is:
```
quit
```

## Extensions

Extensions are a way to change how Bambam behaves.
They are supported since version 1.3.0, currently as an **experimental** feature.

Extensions are directories containing media files as well as a file describing how the game should behave when a certain event happens. Anyone can [create an extension](EXTENSIONS.md), it _does not_ require programming skills.

Currently there is only a single extension bundled with the game:
- [`alphanumeric-en_US`](./extensions/alphanumeric-en_US/) - this extension makes the program play recordings of American English pronounciation of letters and digits when the corresponding keys are pressed.

To use an extension:
1. Make sure the extension directory is located in one of the extension base directories, that is:
   - `extensions/` in the same directory as the bambam program,
   - `$HOME/.local/share/bambam/extensions/`,
   - `/usr/share/bambam/extensions/` - if the program is installed from your distribution's package.
2. Pass the `--extension` option followed by the name of the extension on program invocation.

   For example `./bambam.py --extension alphanumeric-en_US`.

See [separate documentation on creating extensions](EXTENSIONS.md) if you would like to create your own extension or change an existing one.

## More information

More information is in the manual page. To view it, type:
```
man ./bambam.6
```

Comments or suggestions? Any feedback is appreciated, please send it to [the bambam-users forum](https://groups.google.com/forum/#!forum/bambam-users).

Translations for this game are done on [Weblate](https://hosted.weblate.org/projects/bambam/). Please help translating for your mother tongue!

## History

This project was moved from [its code.google.com location](https://code.google.com/p/bambam/) in April 2015, since that site was about to be shut down.

Note that changes (as of 2010-08-17) from [the launchpad bambam fork](https://launchpad.net/bambam) had been merged back to this project in February 2014.

The sounds for the alphanumeric-en_US extension were copied from https://github.com/porridge/bambam-media and are distributed
under the terms of the GNU General Public License.
