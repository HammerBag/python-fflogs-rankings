import os,time
import pandas as pd
import numpy as np #May not actually be needed... think pandas imports this as a dependancy
#Global vars. Grab the API key from .env and set the debug mode 
api_key = os.getenv('KEY')
#Static vars. These would be changed manually when either the fights change, or new data is considered/deprecated
fight_list =['Phantom Train','Demon Chadarnook','Guardian','Kefka','God Kefka']
filter_list=['startTime','class','server','estimated','outOf','ilvlKeyOrPatch','characterID','difficulty','fightID','characterName','rank']
#Function to return the region where a server is located

def to_int(num):
	return int(num)

def get_server_region(server):
	"""Returns the DataCenter/Region where a server is located.
	
	Server Region is required for submitting request to the API"""
	server_ref={
		'NA':[
			'adamantoise','balmung','cactuar','coeurl','faerie','gilgamesh','goblin','jenova','mateus','midgardsormr','sargatanas','siren','zalera','behemoth','brynhildr','diabolos','excalibur','exodus','famfrit','hyperion','lamia','leviathan','malboro','ultros'
		],
		'EU':[
			'cerberus','lich','louisoix','moogle','odin','omega','phoenix','ragnarok','shiva','zodiark',
		],
		'JP':[
			'anima','asura','belias','chocobo','hades','ixion','mandragora','masamune','pandaemonium','shinryu','titan','aegis','atomos','carbuncle','garuda','gungnir','kujata','ramuh','tonberry','typhon','unicorn','alexander','bahamut','durandal','fenrir','ifrit','ridill','tiamat','ultima','valefor','yohimbo','zeromus'
		]
	}
	for region in server_ref.keys():
		if server in server_ref[region]:
			#Return the region the server belongs in if there is one
			#If it doesn't exist, the function will just return 'None'
			return region 
#Function to retrieve and format the API/ranking results
def get_results(sorted_data,fightlist,speclist,sorting = 'percentile'):
	"""Returns the best values for each fight in fightlist, for each job in speclist.
	
	Uses the specified sorting method. Default is 'percentile'."""
	output = pd.DataFrame({'duration':[],'encounterID':[],'encounterName':[],'percentile':[],'reportID':[],'spec':[],'total':[]},dtype=object)
	#Sets the output as a blank DataFrame.
	for y in range(0,len(fightlist)):
		#For each fight, run through the list and filter out that fight.
		sample = sorted_data.loc[(sorted_data['encounterName'] == fightlist[y])]
		sample.reset_index(drop=True,inplace=True) #Filters the fight then resets index 0-n
		for x in range(0,len(speclist)):
			#After filtering for just fight, iterate through and grab the highest value
			if sorting == 'total' or sorting == 'percentile':
				temp = sample.loc[(sample['spec'] == speclist[x])].nlargest(1,sorting)
			elif sorting == 'duration':
				#When looking for speed of kill, lowest value is preferable.
				temp=sample.loc[(sample['spec'] == speclist[x])].nsmallest(1,sorting)
			else:
				break
			if not temp.empty:
				output = pd.concat([output,temp],axis=0,ignore_index=True)
			else:
				pass
	for n in range(0,output.shape[0]):
		#Since 'duration' is in ms format, before returning the dataframe,
		#iterate through and convert 'duration' to MM:SS format.
		output.at[n,'duration'] = time.strftime('%M:%S',time.gmtime(output.at[n,'duration']/1000))
	output = output.sort_values(['encounterID',sorting],ascending=[True,False])
	output['percentile'] = pd.to_numeric(output['percentile']) #convert percentile (dtype = object) to numeric data (dtype=intxx)
	output.reset_index(drop=True,inplace=True) #Since we sorted, reset the index order (0-max)
	return output

#Program loop if running by itself.
"""
!!IMPORTANT!!
When integrating this into another program, you would need to adjust the name and server inputs, but leave the rest intact (or skip name/server, and pass the URL).
For example, in a discord bot, you may already have the first+last+server name, and can either pass those values directly, or pass the full url. Then you just need a method to output the data in a neat format.

For myself, when I do my discord bot, will have to adjust the data to output into an embed. """
while __name__ == '__main__':
	name = input ("Type in Name>>> ")
	name = name.replace(" ","%20") #Replace spaces so that they can be read as a URL
	#NOTE: Need to add additional formatting to fix all punctuation options like ' and `
	server = input ("Type in Server>>> ") #'Jenova'
	region = get_server_region(server)
	filename = name.replace('%20',' ')+'-'+server
	open(filename+'.txt','a').close()
	print (filename)
	#if region is not None:
	#	break
	#URL requires name,server, and region inputs. Easier to adjust it here because the JSON request line just looks cleaner.
	url = 'https://www.fflogs.com:443/v1/parses/character/'+name+'/'+server+'/'+region+'?timeframe=historical&metric=dps&api_key='+api_key
	print (url)
	try:
		fflogsData = pd.read_json(url)
	except Exception:
		pause = input("Got a bad request from the FFLogs server. Check the data entered.\n\nPress any key to continue.")
		continue

	fflogsData.drop(filter_list,axis=1,inplace=True) #Drop all values that are not useful.
	#fflogsData.to_csv(path_or_buf='output2.txt',index=False,header=True)
	spec_list =[] #spec = job in the API. Create a blank list and then fill it in.
	for x in range(0,fflogsData.shape[0]):
		#Build a list of jobs the player has cleared any content with
		if fflogsData.loc[x,'spec'] not in spec_list:
			spec_list.append(fflogsData.loc[x,'spec'])
	sort_by = input ('Sort by? (Options: \"time\",\"dps\", or \"percentile\") >>>')
	print (f'sorting values by {sort_by.lower()}. Please wait...')
	if sort_by.lower() == 'time':
		sort_by = 'duration'
	elif sort_by.lower() == 'percentile' or sort_by == '':
		sort_by = sort_by.lower()
		print (sort_by)
	elif sort_by.lower() == 'dps':
		sort_by = 'total'
	elif sort_by is None:
		sort_by = 'percentile'
	else:
		pause = input("Invalid Selection. Press any key to try again.")
		continue

	final_data = get_results(fflogsData,fight_list,spec_list,sort_by)
	final_data.to_csv(path_or_buf=filename+'.txt',sep=' ',index=False,header=False) #Just for fun, output to a .txt file. That way, the columns aren't cut off

	print(final_data)
	print('\n\nTop 3 Jobs by fight:')
	for x in fight_list:
		if final_data.loc[(final_data['encounterName'] == x)].shape[0] <1:
			pass
		else:		
			print (x)
			print (final_data.loc[(final_data['encounterName'] == x)].nlargest(3,sort_by))
	pause = input (">>Press any key to continue")