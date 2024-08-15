import joblib
import numpy as np

sensor_anomaly_model = joblib.load('C:/Users/Usman/smart-retail/sensor_anomaly_model.pkl')
device_status_model = joblib.load('C:/Users/Usman/smart-retail/device_status_model.pkl')


def predict_sensor_anomaly(sensor_reading):

    data_for_prediction = np.array([[sensor_reading]])
    prediction = sensor_anomaly_model.predict(data_for_prediction)
    return prediction[0] == -1


def predict_device_status(device_features):

    data_for_prediction = np.array([device_features])
    prediction = device_status_model.predict(data_for_prediction)
    return prediction[0]
