# Get pitch points at a fixed step from the domains of interest

form Calculate durations of labeled segments
	sentence openpathTextGrid E:\UU\4.Experiments\Exp2\Analysis\TextGrid_TargetA_6tiers_addBoundaris_addLabels_addTier1label_addSylNoTier1_addPointTier6\1-11
	sentence openpathPitchTier E:\UU\4.Experiments\Exp2\Analysis\PitchTier_Double_corrected
	comment Which tier of the TextGrid object would you like to analyse?
	integer textTier 1
	integer dOITier 4
	# dOI = domain Of Interest
	# integer pitchPointNumber 10
	comment Where do you want to save the results?
	text textfile E:\UU\4.Experiments\Exp1\Analysis\Results\FPCA\FPCA_NH\data\E2_S1_pitch\
endform

if right$(openpathTextGrid$,1)<>"\"
	openpathTextGrid$ = openpathTextGrid$+"\"
endif

if right$(openpathPitchTier$,1)<>"\"
	openpathPitchTier$ = openpathPitchTier$+"\"
endif

Create Strings as file list... tg_list 'openpathTextGrid$'*.TextGrid
Create Strings as file list... pt_list 'openpathPitchTier$'*.PitchTier

select Strings tg_list
numberOftgFiles = Get number of strings

select Strings pt_list
numberOfptFiles = Get number of strings

titleline$ = "tgsimpleName tglabel time tempTime f0 'newline$'"
#fileappend "'textfile$'" 'titleline$'
# to be consistent with how Gubian coded his data, change time0 to time in the header.


for tgfile from 1 to numberOftgFiles
	select Strings tg_list
	tgfileName$ = Get string... 'tgfile'
	tgsimpleName$ = tgfileName$ - ".TextGrid"
	tgtextGridName$ = tgsimpleName$ + ".TextGrid"
	textfiledir$ = textfile$ + tgsimpleName$ + ".txt"
	fileappend "'textfiledir$'" 'titleline$'
	#These steps are crucial, cuz .TextGrid in Praat window do not have the suffix ".TextGrid"
	
	Read from file... 'openpathTextGrid$''tgfileName$'
	select TextGrid 'tgsimpleName$'
	tglabel$ = Get label of interval... textTier 2

	numberOfdOIIntervals = Get number of intervals... dOITier
	if numberOfdOIIntervals > 2
		select TextGrid 'tgsimpleName$'
		dOILabel$ = Get label of interval... dOITier 2
		dOIstart = Get starting point... dOITier 2
		dOIend = Get end point... dOITier 2
		dOIduration = dOIend - dOIstart
		pitchPointNumber = dOIduration/0.01
		pitchPointNumberInt$ = fixed$(pitchPointNumber, 0)
		pitchPointNumberInt = number(pitchPointNumberInt$)
		# tempNum = pitchPointNumber - 1
		# stepTime = dOIduration/tempNum
		

		for ptfile from 1 to numberOfptFiles
			select Strings pt_list
			ptfileName$ = Get string... 'ptfile'
			ptsimpleName$ = ptfileName$-".PitchTier"
			ptName$ = ptsimpleName$+".PitchTier"
			
			if ptsimpleName$ = tgsimpleName$
				Read from file... 'openpathPitchTier$''ptfileName$'
				select PitchTier 'ptsimpleName$'
				To Pitch: 0.02, 60, 600
				
					for pitchPoint from 0 to pitchPointNumberInt
					temptTime = dOIstart + 0.01*pitchPoint
					time0 = 0.01*pitchPoint*1000
					time0$ = fixed$(time0, 0)
					time0 = number(time0$)
						if temptTime >= dOIstart and temptTime <= dOIend
						select Pitch 'ptsimpleName$'
						pitchValue = Get value at time: temptTime, "semitones re 1 Hz", "Linear"
						pitchValue$ = fixed$(pitchValue, 2)
						pitchValue = number(pitchValue$)
						# pitchPointListed = pitchPoint+1


						resultline$ = "'tgsimpleName$' 'tglabel$' 'time0' 'temptTime' 'pitchValue' 'newline$'"
						fileappend "'textfiledir$'" 'resultline$'
						endif
					endfor
			
			select PitchTier 'ptsimpleName$'
			Remove
			select Pitch 'ptsimpleName$'
			Remove
			endif
		endfor
	endif
select TextGrid 'tgsimpleName$'
Remove

endfor

select Strings tg_list
Remove

select Strings pt_list
Remove
