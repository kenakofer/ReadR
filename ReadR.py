#!/usr/bin/python3

#TODO speed isn't accurate, context showing on pause, maybe add focus letter.


from time import sleep
import sys
import os
import tty
import termios
import threading
import argparse

bookmarks_file = os.path.dirname(os.path.realpath(__file__))+'/bookmarks'
parser=argparse.ArgumentParser(description='User-friendly colorful command line speed reader, focused on comprehension, written in python.')
parser.add_argument('FILE', type=argparse.FileType('r'), action='store', help='The text file to read')
parser.add_argument('-w', '--wpm', type=int, action='store', default=350, help='The words per minute at startup. Default 350')
parser.add_argument('-p', '--phrase-length', type=int, action='store', default=7, help='The max number of summed characters (non-whitespace) that triggers clumping of short phrases, like "I am a". Default 7')
parser.add_argument('-s', '--steady-speed', action='store_true', help="Do not give special calculation to a phrase's display time, but show each phrase strictly for 60/wpm seconds")
parser.add_argument('-c', '--color-quotes', action='store_true', help='Colors the text inside quotation marks ("...") differently')
parser.add_argument('-m', '--minimalist', action='store_true', help='Remove the interface. Keep only the flashing words. Note that this does not affect any of the controls, or color.')
args = parser.parse_args()
file_name=args.FILE.name.split('/')[-1]
ALL_WORDS=[]		#Loads every word in the file for easy navigation later
word_queue=[]		#The lineup of words to be printed on the screen, with the word at [0] being next.
phrase=''		#The current phrase being displayed, with every edit and format
line_num=0		#The current line in the file
word_num=0		#Word counter
time_elapse=0		#Cumulative time delay
quotes=0		#Whether the reading is inside quotes, for the highlight_speech option. 0 is outside, 1 is inside, 2 is inside, but on the last phrase.
wpm=args.wpm		#Approximate words per minute, though exact delays on words will vary with commonality or length.
wpm_calib=1.56		#Assists with keeping the average wpm close to the above value.  This will vary based on wpm and the format and style of the work.
paused=False
chars_in_phrase=args.phrase_length	#If neighboring words contain these or fewer characters, they will be lumped into one printed phrase, such as 'in the' or 'I was in'.  spaces don't count
line_pause=200/wpm	#How long (extra) to pause when an empty line (usually indicates a new paragraph or speaker) is encountered
sentence_pause=80/wpm	#How long (extra) to pause at the end of a sentence (at . ." ? ?")
highlight_speech=args.color_quotes	#Changes color of the printed text if inside quotes, eg "...".
minimalist=args.minimalist		#Removes the pretty interface
steady_speed=args.steady_speed		#Gives all phrases equal time.

offset=22

#Useful terminal definitions
NONE='\033[00m'
RED='\033[01;31m'
GREEN='\033[01;32m'
YELLOW='\033[01;33m'
PURPLE='\033[01;35m'
CYAN='\033[01;36m'
WHITE='\033[01;37m'
BOLD='\033[1m'
UNDERLINE='\033[4m'

#Alter these for color and style alterations
BORDER=NONE
FOCUSLINE=GREEN
CONTROLS=PURPLE
TEXT=WHITE+BOLD
QUOTE=CYAN
STATUSLINE=NONE


#Inputs the whole file to an array, for easy navigation
def load_words():
	global ALL_WORDS
	for line in f:
		line = line.replace('  ',' ').strip()
		if line == '':
			if nl<2:
				ALL_WORDS.append('<NEWLINE>')
			nl+=1
		else:
			nl=0
			ALL_WORDS+=line.split()

#Prepares words from the ALL_WORDS array for imminent display.
def fill_word_queue(words):
	global word_queue, word_num
	if word_num<0:
		word_num=0
		word_queue.append('________BEGINNING_OF_FILE________')
	elif word_num>=len(ALL_WORDS)-1:
		word_num=len(ALL_WORDS)-1
		word_queue.append('___________END_OF_FILE___________')
	else:
		try:
			for i in range(words):
				word_queue.append(ALL_WORDS[word_num])
				word_num+=1
		except IndexError:
			word_num=len(ALL_WORDS)-1
			word_queue.append('___________END_OF_FILE___________')


#Uses the word queue to decide how much to put in a phrase (which is printed at once on the screen)
def build_phrase():
	global word_queue, chars_in_phrase, quotes, highlight_speech

	#First, make sure there are enough words loaded
	while len(word_queue) < 10:
		fill_word_queue(10)
	phrase=str(word_queue.pop(0).strip())
	#If the next word(s) are short, combine them into one phrase
	try:
		while phrase!='<NEWLINE>' and len(phrase)+len(word_queue[0])<chars_in_phrase and \
				word_queue[0]!='<NEWLINE>' and not phrase.endswith('.') and not phrase.endswith('?') and not phrase.endswith('"'):
			phrase+=' '+word_queue.pop(0).strip()
	except IndexError:
		1;
	if highlight_speech:
		#The previously displayed phrase was the end of a quote, so turn off highlighting now.
		if quotes==2:
			quotes=0
		#Check for starting or ending quotations
		if phrase.startswith('"'):
			quotes=1
		if phrase.endswith('"') or (len(phrase)>=2 and phrase[-2]=='"'):
			quotes=2
	return phrase
	
#Returns the length of time (in seconds) for the phrase to display
def get_delay(phrase):
	global wpm, line_pause, word_num, time_elapse, wpm_calib, steady_speed
	if steady_speed:
		return 60/wpm
	if phrase=='<NEWLINE>':
		return line_pause
	words=len(phrase.split(' '))
	#word_num+=words
	chars=len(phrase)
	time=words/(wpm*wpm_calib)*60  #All words equal, this is the time the phrase should be displayed for (in seconds).
	time*=.8**(words-1) #Cut off a bit of time for phrases like 'I was a'. This allows for some extra time on bigger words (next line)
	time*=1.07**(chars) #Add a little bit of time for the longer words.
	if phrase.endswith('.') or phrase.endswith('?') or phrase.endswith(';') or phrase.endswith('"'):
		time*=1.2
	return time

#Adds padding and pretty formatting to the phrase margins
def phrase_format(o, p):
	global STATUSLINE, QUOTE, TEXT, BORDER, quotes
	phrase=p
	if phrase=='<NEWLINE>':
		phrase=' '*2*(offset+1)
	#center the phrase with spaces on either side.  Note that it does not currently center on a vowel in the phrase, as some software does.
	else:
		i=0
		while i <= (o-len(p)/2):
			phrase=' '+phrase+' '
			i+=1
		if len(phrase)%2==1:
			phrase+=' '
	
	#Additional formatting, including different colored quotes
	if quotes!=0:
		phrase=QUOTE+phrase+NONE
	else:
		phrase=TEXT+phrase+NONE
	#Add the context of the application format, with borders, and status on the sides
	if not minimalist:
		phrase=BORDER+'|'+phrase+'|'+STATUSLINE+UNDERLINE+' WPM: '+str(int(actual_wpm+.5))+', WordNum: '+str(word_num-5)
	if word_num>5: 
		for i in range(0,6-len(str(word_num-5))):
			phrase+=' '
	if not minimalist:
		phrase+=BORDER+'|'

	return phrase

#Listens for key presses in the terminal
def get_character():
	fd = sys.stdin.fileno()
	old_settings = termios.tcgetattr(fd)
	try:
	    tty.setraw(sys.stdin.fileno())
	    ch = sys.stdin.read(1)
	finally:
	    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
	return ch

#Parses key presses for commands
def command_listener():
	global wpm, paused, word_num, bump
	sleep(.5)
	while True:
		char=str(get_character()).lower()
		if char=='+':
			wpm+=5
		elif char=='-':
			wpm-=5
		elif char=='p':
			paused=not paused
		elif char=='q':
			write_bookmarks()
			os._exit(0)
		elif char=='.':
			del word_queue[:]
			word_num+=45
			if paused:
				bump=True
		elif char==',':
			del word_queue[:]
			word_num-=55
			if paused: 
				bump=True
		elif char=='>':
			del word_queue[:]
			word_num+=195
			if paused:
				bump=True
		elif char=='<':
			del word_queue[:]
			word_num-=205
			if paused: 
				bump=True
		calib_wpm(3)

			#print('Unknown character:',char)

#Formats the interface
def setup():
	global phrase, BORDER, FOCUSLINE, CONTROLS
	if not minimalist:
		os.system('clear')
	#	sys.stdout.write(BORDER+CONTROLS+'Q:quit | P:pause | +/-:wpm up/down | >/<:Move 200 words forward/backward | ./,:Move only 50 words\n') 
		sys.stdout.write(BORDER+UNDERLINE+' ReadR_v_1_2_1_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _\n')
		sys.stdout.write(BORDER+'|                   '+FOCUSLINE+'   |   '+BORDER+'                    |'+CONTROLS+'+/-  wpm up/down\n')
		sys.stdout.write(BORDER+'|                   '+FOCUSLINE+'   |   '+BORDER+'                    |'+CONTROLS+'./,  50  words back/forward\n')
		sys.stdout.write(BORDER+'|                   '+FOCUSLINE+'   |   '+BORDER+'                    |'+CONTROLS+'</>  200 words back/forward\n')
		sys.stdout.write(BORDER+'|                   '+FOCUSLINE+'   |   '+BORDER+'                    |'+CONTROLS+'P    pause\n')
		sys.stdout.write(BORDER+'|                   '+FOCUSLINE+'   |   '+BORDER+'                    |'+CONTROLS+'Q    quit\n')
		sys.stdout.write(BORDER+'|                   '+FOCUSLINE+'   |   '+BORDER+'                    |___________________________\n')
		sys.stdout.write(BORDER+phrase)


#Each iteration improves the accuracy of wpm_calib, by scanning through the document with the current settings, and recording the "time" it took.  Its proportional error compared to the desired wpm is used to improve the wpm_calib. 4 times seems to be enough to get within .5 wpm of desired.
def calib_wpm(iterations):
	global wpm, wpm_calib, word_num, actual_wpm, word_queue, calibrating, quotes
	calibrating=True
	save_word_queue=[]
	save_word_queue+=word_queue
	del word_queue[:]
	save_word_num=word_num
	save_quotes=quotes
#	word_num=0
	time_elapse=0
	phrase=''
	count=0
	while count < 200 and phrase !='___________END_OF_FILE___________':
		phrase=build_phrase()
		if phrase != '<NEWLINE>':
			count+=len(phrase.split())
		delay=get_delay(phrase)
		time_elapse+=delay
	actual_wpm=count/time_elapse*60
	wpm_calib=wpm_calib*(wpm/actual_wpm)
	#print('WPM:',wpm,'Actual:',actual_wpm)
	#print('Recalibrated WPM: ',wpm_calib)
	word_num=save_word_num
	quotes=save_quotes
	del word_queue[:]
	word_queue+=save_word_queue
	iterations-=1
	if iterations<=0 or abs(wpm-actual_wpm)<1:
		calibrating=False
		return
	else:
		calib_wpm(iterations)

#Clears the line, and prints the new phrase.
def print_phrase():
	global phrase
	sys.stdout.write('\r')		#Move cursor to beginning of line
	sys.stdout.write(phrase)
	sys.stdout.flush()		#Causes the change to have effect, since there was no line break.

def write_bookmarks():
	global word_num, bookmarks
	try:
		bookmarks[file_name] = word_num
		writer = open(bookmarks_file, 'w')
		for i in range(0,len(bookmarks)):
			writer.write(sorted(bookmarks.keys())[i]+'\t'+str(sorted(bookmarks.values())[i])+'\n')
		writer.close()
	except PermissionError:
		print()
		print()
		print('You do not have write permission for bookmarks file \''+bookmarks_file+'\'. You most allow write access to save bookmarks')

def load_bookmarks():
	global bookmarks, word_num;
	try:
		bookmarks={}
		for line in open(bookmarks_file, 'r'):
			bookmarks[line.split()[0]] = int(line.split()[1])
			if line.split()[0]==file_name:
				word_num = int(line.split()[1])-25
	except PermissionError:
		print('Was unable to read the bookmarks file')
	except FileNotFoundError:
		print('Bookmarks file does not exist. It will be created on exit.')




#MAIN
threading.Thread(target=command_listener).start()
load_bookmarks()
f=args.FILE
load_words()
quotes=0
calib_wpm(6)
i=0
print('Press Q to quit...')
print('')
setup()
bump=False
calibrating=False
while True:
	while paused:
		sleep(.1)
		if bump:
			break
		if not paused:
			sleep(.1)
	while calibrating:
		sleep(.05)
	bump=False
	phrase=build_phrase()
	delay=get_delay(phrase)
	phrase=phrase_format(offset, phrase)
	threading.Thread(target=print_phrase).start()	#This saves a slight amount of time error in maintaining wpm.
	sleep(delay)
