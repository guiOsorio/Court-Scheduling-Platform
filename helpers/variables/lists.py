from helpers.funcs.actions.gets import getRegPossibleTimes, getRegCourts

# Arrays for SelectField choices
numofpeople = ["Not specified", "2", "3", "4"]

courts = getRegCourts(3)

courts_all = getRegCourts(3, True)

possibletimes = getRegPossibleTimes(9, 22)

possibletimesweekend = getRegPossibleTimes(9, 20)