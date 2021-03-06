import yaml
import subprocess
import sys

def transpose(list):
    return [[row[i] for row in list] for i in range(len(list[0]))]


# Step 0,1: Setting everything up and re-writing the .mpc file
mpc_file_path = "runLR.mpc"
settings_map = None

with open(sys.argv[1], 'r') as stream:
    try:
        settings_map = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

alice_data = []
bob_data = []

with open(settings_map['alice_data_path'], 'r') as stream:
    for line in stream:
        # [1:] ignores id
        alice_data.append(line.split(",")[1:])

# remove headers
alice_data = alice_data[1:]

with open(settings_map['bob_data_path'], 'r') as stream:
    for line in stream:
        # [1:] ignores id
        bob_data.append(line.split(",")[1:])

# remove headers
bob_data = bob_data[1:]

# make labels/feature data disjoint
alice_data = transpose(alice_data)
alice_labels = alice_data[0]

# binarize label (as float)
for i in range(len(alice_labels)):
    label = alice_labels[i]
    if label == "Wild Type":
        alice_labels[i] = "1.0"
    else:
        alice_labels[i] = "0.0"

alice_data = transpose(alice_data[1:])

# binarize data (as float)
for i in range(len(alice_data)):
    row = alice_data[i]

    for j in range(len(row)):
        val = row[j].replace("\n", '')

        if val == "1":
            alice_data[i][j] = "1.0"
        else:
            alice_data[i][j] = "0.0"

bob_data = transpose(bob_data)
bob_labels = bob_data[0]

# binarize label (as float)
for i in range(len(bob_labels)):
    label = bob_labels[i]
    if label == "Wild Type":
        bob_labels[i] = "1.0"
    else:
        bob_labels[i] = "0.0"

bob_data = transpose(bob_data[1:])

# binarize data (as float)
for i in range(len(bob_data)):
    row = bob_data[i]

    for j in range(len(row)):
        val = row[j].replace("\n", '')

        if val == "1":
            bob_data[i][j] = "1.0"
        else:
            bob_data[i][j] = "0.0"

# 'command line arguments' for our .mpc file
alice_examples = len(alice_data)
bob_examples = len(bob_data)
n_features = len(alice_data[0])
n_epochs = settings_map['n_epochs']
folds = settings_map['folds']

file = []
found_delim = False
start_of_delim = 0

i = 0
with open(mpc_file_path, 'r') as stream:
    for line in stream:

        if not found_delim and "@args" in line:
            start_of_delim = i
            found_delim = True
        i += 1

        file.append(line)

file[start_of_delim + 1] = "alice_examples = {n}\n".format(n=alice_examples)
file[start_of_delim + 2] = "bob_examples = {n}\n".format(n=bob_examples)
file[start_of_delim + 3] = "n_features = {n}\n".format(n=n_features)
file[start_of_delim + 4] = "n_epochs = {n}\n".format(n=n_epochs)
file[start_of_delim + 5] = "folds = {n}\n".format(n=folds)

# file as a string
file = ''.join([s for s in file])

# print(file)

with open(mpc_file_path, 'w') as stream:
    stream.write(file)


# Step 2: write to Alice's and Bobs private input files
with open(settings_map['alice_private_input_path'], 'w') as stream:

    str = ""

    for row in alice_data:
        str += " ".join(row) + " "

    str += " ".join(alice_labels)

    stream.write(str)

    if "  " in str:
        raise Exception("Double space")


print("Alice has {n} many private values".format(n=len(alice_data) * len(alice_data[0]) + len(alice_labels)))

with open(settings_map['bob_private_input_path'], 'w') as stream:

    str = ""

    for row in bob_data:
        str += " ".join(row) + " "

    str += " ".join(bob_labels)

    stream.write(str)

    if "  " in str:
        raise Exception("Double space")


print("Bob has {n} many private values".format(n=len(bob_data) * len(bob_data[0]) + len(bob_labels)))

# Step 3: Compile .mpc program
subprocess.call(settings_map['path_to_this_repo'] + "/bash_scripts/compile.sh")

