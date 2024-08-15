import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression


sensor_data_train = np.array([
   [10.0], [10.1], [9.9], [10.2], [10.3],
   [20.0], [22.0], [19.5]
])

device_status_train = np.array([
    [0, 1], [1, 0], [1, 1], [0, 0]
])

device_status_labels = np.array([0, 1, 1, 0])

sensor_anomaly_model = IsolationForest(contamination=0.2)
sensor_anomaly_model.fit(sensor_data_train)

device_status_model = LogisticRegression()
device_status_model.fit(device_status_train, device_status_labels)

joblib.dump(sensor_anomaly_model, 'sensor_anomaly_model.pkl')
joblib.dump(device_status_model, 'device_status_model.pkl')
