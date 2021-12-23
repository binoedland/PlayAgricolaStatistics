# PlayAgricolaStatistics

Data and code for calulating power of Agricola cards at play-agricola.com

The file /Data/2020-2021_pwr.pkl contains a pandas dataframe with each row being a card that was dealt into a 4 player game at play-agricola.com and the data of whether it was drafted, played and so on. This data can be used to calculate ADP and PWR statistics, which is done using the file analyze.stats.py