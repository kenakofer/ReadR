ReadR
=====

ReadR is a python3 command line speed reader for text files, with a user-friendly interface and easy control of the application both in command line arguments and during runtime.  It is a single python3 script file.  Run './ReadR.py --help' for options.

There has recently been a swarm of newly created speed reading applications, even a few terminal-based ones.  How is this one different?

1. Offers an intuitive interface, with a control panel permanently visible by default.  Single character presses can alter wpm and navigation within the document.

2. Adjusts the timing based on word length, punctuation, and paragraph breaks.  This greatly assists in (my) comprehension when speed reading.  The program self-calibrates so that the desired wpm is approximated.  There is always the option to use steady-speed as well.

3. Allows for deciding phrase length (how many words are displayed at once) by number of characters rather than words.  This makes shorter phrases like "I was a" display at once, while long words (which require more comprehensive effort) get their own phrase.  Phrases are designed never to straddle sentences or quotations.

4. Has option to color the inside of quotation marks ("...") differently, using the --color-quotes option.  This is especially useful in the comprehension of novels, when one can easily get lost as the dialogue flies by. 

5. Colorfully formatted interface.  Yes, I know it's a command line application.  The color scheme is easily changed or disabled.

6. Allows for the disabling of the above frivolity, with the --minimalist option.

7. Written in a single short python script, with in-code comments, for easy modification.


Features to add:

1. Option for deciding focus letter.  The current behavior is just to center the phrase, which has not hindered speed or comprehension in my experience.

2. Option to parse command line output instead of a file.

3. A bookmarks file, to record one's position in a larger work.

4. Showing the context of the current phrase when paused, for easier navigation.
