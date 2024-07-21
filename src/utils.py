import pickle

def save_to_pickle(obj, path):
    with open(path, 'wb') as file:
        pickle.dump(obj, file, protocol=pickle.HIGHEST_PROTOCOL)

def read_pickle(path):
    with open(path, 'rb') as file:
        obj = pickle.load(file)
    return obj