﻿import os

os.environ["KERAS_BACKEND"] = "tensorflow"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import numpy as np
import h5py
import keras
import mltools
import rmlmodels.CuDNNLSTMModel as culstm


def to_amp_phase(X_train, X_val, X_test, nsamples):
    X_train_cmplx = X_train[:, :, 0] + 1j * X_train[:, :, 1]
    X_val_cmplx = X_val[:, :, 0] + 1j * X_val[:, :, 1]
    X_test_cmplx = X_test[:, :, 0] + 1j * X_test[:, :, 1]

    X_train_amp = np.abs(X_train_cmplx)
    X_train_ang = np.arctan2(X_train[:, :, 1], X_train[:, :, 0]) / np.pi

    X_train_amp = np.reshape(X_train_amp, (-1, 1, nsamples))
    X_train_ang = np.reshape(X_train_ang, (-1, 1, nsamples))

    X_train = np.concatenate((X_train_amp, X_train_ang), axis=1)
    X_train = np.transpose(np.array(X_train), (0, 2, 1))

    X_val_amp = np.abs(X_val_cmplx)
    X_val_ang = np.arctan2(X_val[:, :, 1], X_val[:, :, 0]) / np.pi

    X_val_amp = np.reshape(X_val_amp, (-1, 1, nsamples))
    X_val_ang = np.reshape(X_val_ang, (-1, 1, nsamples))

    X_val = np.concatenate((X_val_amp, X_val_ang), axis=1)
    X_val = np.transpose(np.array(X_val), (0, 2, 1))

    X_test_amp = np.abs(X_test_cmplx)
    X_test_ang = np.arctan2(X_test[:, :, 1], X_test[:, :, 0]) / np.pi

    X_test_amp = np.reshape(X_test_amp, (-1, 1, nsamples))
    X_test_ang = np.reshape(X_test_ang, (-1, 1, nsamples))

    X_test = np.concatenate((X_test_amp, X_test_ang), axis=1)
    X_test = np.transpose(np.array(X_test), (0, 2, 1))
    return (X_train, X_val, X_test)


classes = ['OOK',
           '4ASK',
           '8ASK',
           'BPSK',
           'QPSK',
           '8PSK',
           '16PSK',
           '32PSK',
           '16APSK',
           '32APSK',
           '64APSK',
           '128APSK',
           '16QAM',
           '32QAM',
           '64QAM',
           '128QAM',
           '256QAM',
           'AM-SSB-WC',
           'AM-SSB-SC',
           'AM-DSB-WC',
           'AM-DSB-SC',
           'FM',
           'GMSK',
           'OQPSK']
from_filename = '/DATASET.hdf5'
f = h5py.File(from_filename, 'r')  # 打开h5文件
X = f['X'][:, :, :]  # ndarray(2555904*1024*2)
Y = f['Y'][:, :]  # ndarray(2M*24)
Z = f['Z'][:]  # ndarray(2M*1)
# [N,1024,2]
in_shp = X[0].shape
n_examples = X.shape[0]
n_train = int(n_examples * 0.6)
n_val = int(n_examples * 0.2)
train_idx = list(np.random.choice(range(0, n_examples), size=n_train, replace=False))
val_idx = list(np.random.choice(list(set(range(0, n_examples)) - set(train_idx)), size=n_val, replace=False))
test_idx = list(set(range(0, n_examples)) - set(train_idx) - set(val_idx))
X_train = X[train_idx]
Y_train = Y[train_idx]
X_val = X[val_idx]
Y_val = Y[val_idx]
X_test = X[test_idx]
Y_test = Y[test_idx]
Z_test = Z[test_idx]
X_train, X_val, X_test = to_amp_phase(X_train, X_val, X_test, 1024)

# Set up some params
nb_epoch = 10000  # number of epochs to train on
batch_size = 400  # training batch size
print(batch_size)
model = culstm.LSTMModel(weights=None, input_shape=[1024, 2], classes=24)
model.compile(loss='categorical_crossentropy', metrics=['accuracy'], optimizer='adam')
model.summary()

filepath = 'weights/weights.h5'
history = model.fit(X_train,
                    Y_train,
                    batch_size=batch_size,
                    epochs=nb_epoch,
                    verbose=2,
                    validation_data=(X_val, Y_val),
                    callbacks=[
                        keras.callbacks.ModelCheckpoint(filepath, monitor='val_loss', verbose=1, save_best_only=True,
                                                        mode='auto'),
                        keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, verbose=1, patince=5,
                                                          min_lr=0.000001),
                        keras.callbacks.EarlyStopping(monitor='val_loss', patience=50, verbose=1, mode='auto')
                        # keras.callbacks.TensorBoard(log_dir='./logs/',histogram_freq=1,write_graph=False,write_grads=1,write_images=False,update_freq='epoch')
                    ]
                    )
mltools.show_history(history)

# Show simple version of performance
score = model.evaluate(X_test, Y_test, verbose=1, batch_size=batch_size)
print(score)


def predict(model):
    model.load_weights(filepath)
    # Plot confusion matrix
    test_Y_hat = model.predict(X_test, batch_size=batch_size)
    cm, right, wrong = mltools.calculate_confusion_matrix(Y_test, test_Y_hat, classes)
    acc = round(1.0 * right / (right + wrong), 4)
    print('Overall Accuracy:%.2f%s / (%d + %d)' % (100 * acc, '%', right, wrong))
    mltools.plot_confusion_matrix(cm, labels=['OOK',
                                              '4ASK',
                                              '8ASK',
                                              'BPSK',
                                              'QPSK',
                                              '8PSK',
                                              '16PSK',
                                              '32PSK',
                                              '16APSK',
                                              '32APSK',
                                              '64APSK',
                                              '128APSK',
                                              '16QAM',
                                              '32QAM',
                                              '64QAM',
                                              '128QAM',
                                              '256QAM',
                                              'AM-SSB-WC',
                                              'AM-SSB-SC',
                                              'AM-DSB-WC',
                                              'AM-DSB-SC',
                                              'FM',
                                              'GMSK',
                                              'OQPSK'], save_filename='figure/lstm3_total_confusion.png')
    mltools.calculate_acc_cm_each_snr(Y_test, test_Y_hat, Z_test, classes, min_snr=0)


predict(model)
