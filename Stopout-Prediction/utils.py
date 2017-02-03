import os
import matplotlib.pyplot as plt
import shutil
import numpy as np
import pylab as pl
from feature_dict import *


#TODO: take out once I know for sure i'm not using it
#def sql_to_python_add_default_values(data):
    ##data = [(user_id, feature_week, feature_id, feature_value),
    ##        ()...
    ##        ]
    ##returns [value, value, value...]
    ##return list is same len as input data
    #return_data = []
    #for feature in data:
        #feature_id = feature[2]
        #feature_value = feature[3]
        #default_value = featureDict[feature_id]['default']
        #if feature_value == 'NULL':
            #return_data.append(default_value)
        #else:
            #return_data.append(float(feature_value))

def replace_nulls_with_defaults(features, row):
    return_row = row
    num_weeks = len(row)/len(features)
    week_range = range(num_weeks)
    num_features = len(features)
    for week in week_range:
        start_index = week*num_features
        for f_idx, feature in enumerate(features):
            row_idx = start_index + f_idx
            if row[row_idx] == 'NULL':
                default_value = featureDict[feature]['default']
                return_row[row_idx] = default_value
            else:
                return_row[row_idx] = float(row[row_idx])
    return return_row



def convert_list_to_str(input_list):
    return str(input_list)[1:-1]


def write_inCSV(data,header,out_put_file):
    print "Start writing"
    with open(out_put_file, 'wb') as csv_file:
            writer = csv.writer(csv_file, delimiter = ',',quoting=csv.QUOTE_MINIMAL)#, quoting = csv.QUOTE_ALL)
            if header!=-1:
                writer.writerow(header)
            for line in data:
                writer.writerow(line)
    print "End writing"

def extractArray_fromCSV(csv_file,skip_header):
    data=list()
    with open(csv_file, 'r') as csv_file:
            reader= csv.reader(csv_file, delimiter = ',')
            if skip_header:
                next(reader,None)
            for row in reader:
                line=list()
                for x in row:
                    if x=='NULL':
                        line.append(0)
                    else:
                        line.append(float(x))
                data.append(line)
    return np.array(data)

def create_perStudent_dictionnary(data):
    concat_data={}
    features=list()
    weeks=list()
    for row in data:
        print row
        stud=row[2]
        if stud not in concat_data:
            concat_data[stud]={}
        week=row[3]
        print week
        if int(float(week)) not in range(16):
            continue
        if week not in weeks:
            weeks.append(week)
        if week not in concat_data[stud]:
            concat_data[stud][week]={}
        feature_id=row[1]
        if feature_id not in features:
            features.append(feature_id)
        if row[4]=='\N':
            concat_data[stud][week][feature_id]=0
        else:
            concat_data[stud][week][feature_id]=row[4]
    return weeks,features,concat_data

def create_formatData_fromDict(weeks,features,concat_data):

    concat_data2=list()
    concat_data2.append(['week_id']+features)

    for stud in concat_data:
        for week in weeks:
            stud_week_data=[week]
            for feat in features:
                if week in concat_data[stud] and feat in concat_data[stud][week]:
                    stud_week_data.append(concat_data[stud][week][feat])
                else:
                    stud_week_data.append(0)
            concat_data2.append(stud_week_data)
    return concat_data2

def shuffle_unison(X,Y,seed):
    Y=np.reshape(Y,(np.shape(Y)[0],1))
    conc=np.concatenate((X,Y),axis=1)
    np.random.seed(seed)
    np.random.shuffle(conc)
    X_new=conc[:,:-1]
    Y_new=conc[:,-1]
    return X_new,Y_new





def remove_and_make_dir(directory):
	# If the directory exists, remove it
	if os.path.exists(directory):
		shutil.rmtree(directory)
	os.makedirs(directory)

def move_emissions_transitions(source_dir, destination_dir):
	remove_and_make_dir(destination_dir)
	shutil.move(source_dir + "emissions.txt", destination_dir)
	shutil.move(source_dir + "transitions.txt", destination_dir)

def copy_files(files, source_dir, destination_dir):
	for f in files:
		shutil.copyfile(os.path.join(source_dir,f), os.path.join(destination_dir,f))

def add_to_data(old_data, new_data):
	if old_data == None:
		return new_data
	else:
		return np.vstack((old_data, new_data))

def plotROC(fpr, tpr, roc_auc, lead, lag):
	pl.clf()
	pl.plot(fpr, tpr, label='ROC curve (area = %0.3f)' % roc_auc)
	pl.plot([0, 1], [0, 1], 'k--')
	pl.xlim([0.0, 1.0])
	pl.ylim([0.0, 1.0])
	pl.xlabel('False Positive Rate')
	pl.ylabel('True Positive Rate')
	pl.title('ROC- lead = %s lag = %s' % (lead, lag))
	pl.legend(loc="lower right")
	pl.show()

def save_fig(path, ext='png', close=True):
	"""Save a figure from pyplot.

	Parameters
	----------
	path : string
		The path (and filename, without the extension) to save the
		figure to.

	ext : string (default='png')
		The file extension. This must be supported by the active
		matplotlib backend (see matplotlib.backends module).  Most
		backends support 'png', 'pdf', 'ps', 'eps', and 'svg'.

	close : boolean (default=True)
		Whether to close the figure after saving.  If you want to save
		the figure multiple times (e.g., to multiple formats), you
		should NOT close it in between saves or you will have to
		re-plot it.

	"""

	# Extract the directory and filename from the given path
	directory = os.path.split(path)[0]
	filename = "%s.%s" % (os.path.split(path)[1], ext)
	if directory == '':
		directory = '.'

	# If the directory does not exist, create it
	if not os.path.exists(directory):
		os.makedirs(directory)

	# The final path to save to
	savepath = os.path.join(directory, filename)

	# Actually save the figure
	plt.savefig(savepath, dpi=300)

	# Close it
	if close:
		plt.close()
