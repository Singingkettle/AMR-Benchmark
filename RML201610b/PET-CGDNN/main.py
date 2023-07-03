﻿# Import all the things we need ---
#   by setting env variables before Keras import you can set up which backend and which GPU it uses
import os

os.environ["KERAS_BACKEND"] = "tensorflow"
# os.environ["THEANO_FLAGS"]  = "device=gpu%d"%(0)
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import numpy as np
# matplotlib.use('Tkagg')
import matplotlib.pyplot as plt
# from matplotlib import pyplot as plt
import pickle
import keras
from keras.regularizers import *
import csv
import mltools, rmldataset2016
import rmlmodels.PETCGDNN as DLAMRMODEL

# set Keras data format as channels_first
K.set_image_data_format('channels_last')
print(K.image_data_format())

model = DLAMRMODEL.PETCGDNN()
model.compile(loss='categorical_crossentropy', metrics=['accuracy'], optimizer='adam')
model.summary()

(mods, snrs, lbl), (X_train, Y_train), (X_val, Y_val), (X_test, Y_test), (train_idx, val_idx, test_idx) = \
    rmldataset2016.load_data()

X1_train = X_train[:, :, 0]
X1_test = X_test[:, :, 0]
X1_val = X_val[:, :, 0]
X2_train = X_train[:, :, 1]
X2_test = X_test[:, :, 1]
X2_val = X_val[:, :, 1]
X_train = np.expand_dims(X_train, axis=3)
X_test = np.expand_dims(X_test, axis=3)
X_val = np.expand_dims(X_val, axis=3)
print(X_train.shape)
classes = mods

# Set up some params
nb_epoch = 1000  # number of epochs to train on
batch_size = 400  # training batch size

model = DLAMRMODEL.PETCGDNN()
model.compile(loss='categorical_crossentropy', metrics=['accuracy'], optimizer='adam')
model.summary()

filepath = 'weights/weights.h5'
history = model.fit([X_train, X1_train, X2_train],
                    Y_train,
                    batch_size=batch_size,
                    epochs=nb_epoch,
                    verbose=2,
                    validation_data=([X_val, X1_val, X2_val], Y_val),
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
# #Show simple version of performance
score = model.evaluate([X_test, X1_test, X2_test], Y_test, verbose=1, batch_size=batch_size)
print(score)


def predict(model):
    model.load_weights(filepath)
    # Plot confusion matrix
    test_Y_hat = model.predict([X_test, X1_test, X2_test], batch_size=batch_size)
    confnorm, _, _ = mltools.calculate_confusion_matrix(Y_test, test_Y_hat, classes)
    mltools.plot_confusion_matrix(confnorm,
                                  labels=['8PSK', 'AM-DSB', 'BPSK', 'CPFSK', 'GFSK', '4-PAM', '16-QAM', '64-QAM',
                                          'QPSK', 'WBFM'], save_filename='figure/lstm3_total_confusion.png')

    # Plot confusion matrix
    acc = {}
    acc_mod_snr = np.zeros((len(classes), len(snrs)))
    i = 0
    for snr in snrs:
        test_SNRs = [lbl[x][1] for x in test_idx]
        test_X_i = X_test[np.where(np.array(test_SNRs) == snr)]
        test_X1_i = X1_test[np.where(np.array(test_SNRs) == snr)]
        test_X2_i = X2_test[np.where(np.array(test_SNRs) == snr)]
        test_Y_i = Y_test[np.where(np.array(test_SNRs) == snr)]

        # estimate classes
        test_Y_i_hat = model.predict([test_X_i, test_X1_i, test_X2_i])
        confnorm_i, cor, ncor = mltools.calculate_confusion_matrix(test_Y_i, test_Y_i_hat, classes)
        acc[snr] = 1.0 * cor / (cor + ncor)
        result = cor / (cor + ncor)
        with open('acc111.csv', 'a', newline='') as f0:
            write0 = csv.writer(f0)
            write0.writerow([result])
        mltools.plot_confusion_matrix(confnorm_i,
                                      labels=['8PSK', 'AM-DSB', 'BPSK', 'CPFSK', 'GFSK', '4-PAM', '16-QAM', '64-QAM',
                                              'QPSK', 'WBFM'], title="Confusion Matrix",
                                      save_filename="figure/Confusion(SNR=%d)(ACC=%2f).png" % (snr, 100.0 * acc[snr]))

        acc_mod_snr[:, i] = np.round(np.diag(confnorm_i) / np.sum(confnorm_i, axis=1), 3)
        i = i + 1

    # plot acc of each mod in one picture
    dis_num = 10
    for g in range(int(np.ceil(acc_mod_snr.shape[0] / dis_num))):
        assert (0 <= dis_num <= acc_mod_snr.shape[0])
        beg_index = g * dis_num
        end_index = np.min([(g + 1) * dis_num, acc_mod_snr.shape[0]])

        plt.figure(figsize=(12, 10))
        plt.xlabel("Signal to Noise Ratio")
        plt.ylabel("Classification Accuracy")
        plt.title("Classification Accuracy for Each Mod")

        for i in range(beg_index, end_index):
            plt.plot(snrs, acc_mod_snr[i], label=classes[i])
            # 设置数字标签
            for x, y in zip(snrs, acc_mod_snr[i]):
                plt.text(x, y, y, ha='center', va='bottom', fontsize=8)

        plt.legend()
        plt.grid()
        plt.savefig('figure/acc_with_mod_{}.png'.format(g + 1))
        plt.close()
    # save acc for mod per SNR
    fd = open('predictresult/acc_for_mod_on_lstm.dat', 'wb')
    pickle.dump((acc_mod_snr), fd)
    fd.close()

    # Save results to a pickle file for plotting later
    print(acc)
    fd = open('predictresult/lstm.dat', 'wb')
    pickle.dump((acc), fd)

    # Plot accuracy curve
    plt.plot(snrs, list(map(lambda x: acc[x], snrs)))
    plt.xlabel("Signal to Noise Ratio")
    plt.ylabel("Classification Accuracy")
    plt.title(" Classification Accuracy on RadioML 2016.10 Alpha")
    plt.tight_layout()
    plt.savefig('figure/each_acc.png')


predict(model)
