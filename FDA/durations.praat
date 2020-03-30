# This script will calculate the durations of all labeled segments in all TextGrid objects in a folder.
# The results will be save in a text file, each line containing the file name, the label text and the 
# duration of the corresponding segment..
# 
#
# This script is distributed under the GNU General Public License.
# Copyright 12.3.2002 Mietta Lennes
# Modified by Na HU, 20180813

# ask the user for the tier number
form Calculate durations of labeled segments
	sentence openpath E:\UU\4.Experiments\Exp4\Data\TextGrid_words_add boundaries\
	comment Which tier of the TextGrid object would you like to analyse?
	integer Tier 2
	comment Where do you want to save the results?
	text textfile E:\UU\4.Experiments\Exp4\Results\E4_word durations.csv
endform

if right$(openpath$,1)<>"\"
	openpath$=openpath$+"\"
endif


Create Strings as file list... fileList 'openpath$'*.TextGrid
numberOfFiles=Get number of strings

titleline$ = "newlabel label start end duration 'newline$'"
fileappend "'textfile$'" 'titleline$'

for ifile from 1 to numberOfFiles

	select Strings fileList
	fileName$=Get string... 'ifile'
	simpleName$=fileName$-".TextGrid"
	textGridName$=simpleName$+".TextGrid"
	#These steps are crucial, cuz .TextGrid in Praat window do not have the suffix ".TextGrid"
	newlabel$=replace$(simpleName$,"Wave_Target_A_NewLabel_", "", 0)

	Read from file... 'openpath$''fileName$'
	select TextGrid 'simpleName$'

# check how many intervals there are in the selected tier:
	numberOfIntervals = Get number of intervals... tier

# loop through all the intervals
for interval from 1 to numberOfIntervals
	label$ = Get label of interval... tier interval
	# if the interval has some text as a label, then calculate the duration.
	if label$ <> ""
		start = Get starting point... tier interval
		end = Get end point... tier interval
		duration = end - start
		# append the label and the duration to the end of the text file, separated with a tab:		
		resultline$ = "'newlabel$' 'label$' 'start' 'end' 'duration' 'newline$'"
		fileappend "'textfile$'" 'resultline$'
	endif
endfor

	select TextGrid 'simpleName$'
	Remove
endfor