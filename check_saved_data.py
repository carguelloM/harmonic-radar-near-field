import pickle
dir = 'data_test'
with open(dir + '/test_data.pkl', 'rb') as f:
    data = pickle.load(f)

print(data['peaks'])