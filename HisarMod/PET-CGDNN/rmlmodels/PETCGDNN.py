"""CLDNNLike model for RadioML.

# Reference:

- [CONVOLUTIONAL,LONG SHORT-TERM MEMORY, FULLY CONNECTED DEEP NEURAL NETWORKS ]

Adapted from code contributed by Mika.
"""
import os

WEIGHTS_PATH = ('resnet_like_weights_tf_dim_ordering_tf_kernels.h5')
from keras.models import Model
from keras.layers import Input, Dense, concatenate, Flatten, Reshape
from keras.layers.convolutional import Conv2D
from keras.layers import Lambda, Multiply, Add, Subtract, CuDNNGRU
import tensorflow as tf


def cal1(x):
    y = tf.keras.backend.cos(x)
    return y


def cal2(x):
    y = tf.keras.backend.sin(x)
    return y


def PETCGDNN(weights=None,
             input_shape=[1024, 2],
             input_shape2=[1024],
             classes=26,
             **kwargs):
    if weights is not None and not (os.path.exists(weights)):
        raise ValueError('The `weights` argument should be either '
                         '`None` (random initialization), '
                         'or the path to the weights file to be loaded.')

    dr = 0.5  # dropout rate (%)
    input = Input(input_shape + [1], name='input1')
    input1 = Input(input_shape2, name='input2')
    input2 = Input(input_shape2, name='input3')
    # x1 = Flatten()(input)
    # x1 = GaussianNoise(0.1)(x1)
    # x1 = Conv2D(8,(8,2),activation='relu')(input)

    x1 = Flatten()(input)
    # x1 = BatchNormalization()(x1)
    # x1 = Dense(64,name='fc1')(x1)
    # x1 = LeakyReLU(alpha=0.3)(x1)
    # x1 = Dropout(dr)(x1)
    x1 = Dense(1, name='fc2', activation="linear")(x1)
    # x1 = Dropout(dr)(x1)
    # x1 = Reshape(target_shape=(128, 1), name='reshape1')(x1),activation='linear'
    # x2 = Dense(128, name='fc3')(input2)
    # x2 = LeakyReLU(alpha=0.3)(x2)
    # x2 = Dropout(dr)(x2)
    # x2 = Reshape(target_shape=(128, 1), name='reshape2')(x2)
    cos1 = Lambda(cal1)(x1)
    sin1 = Lambda(cal2)(x1)
    x11 = Multiply()([input1, cos1])
    x12 = Multiply()([input2, sin1])
    x21 = Multiply()([input2, cos1])
    x22 = Multiply()([input1, sin1])
    y1 = Add()([x11, x12])
    y2 = Subtract()([x21, x22])
    y1 = Reshape(target_shape=(1024, 1), name='reshape1')(y1)
    y2 = Reshape(target_shape=(1024, 1), name='reshape2')(y2)
    x11 = concatenate([y1, y2])
    x3 = Reshape(target_shape=((1024, 2, 1)), name='reshape3')(x11)

    # SeparateChannel Combined Convolutional Neural Networks
    # spatial feature
    x3 = Conv2D(75, (8, 2), padding='valid', activation="relu", name="conv1_1", kernel_initializer='glorot_uniform')(
        x3)
    x3 = Conv2D(25, (5, 1), padding='valid', activation="relu", name="conv1_2", kernel_initializer='glorot_uniform')(
        x3)
    # temporal feature
    x4 = Reshape(target_shape=((1013, 25)), name='reshape4')(x3)
    # x4 = CuDNNLSTM(units=128, return_sequences=True)(x4)
    x4 = CuDNNGRU(units=128)(x4)

    # x = Dense(128, activation='relu', name='fc4')(x4)
    # x = Dropout(dr)(x)
    # x = GaussianNoise(0.1)(x4)
    x = Dense(classes, activation='softmax', name='softmax')(x4)

    model = Model(inputs=[input, input1, input2], outputs=x)

    # Load weights.
    if weights is not None:
        model.load_weights(weights)

    return model


import keras
from keras.utils.vis_utils import plot_model

if __name__ == '__main__':
    model = PETCGDNN(None, classes=10)

    adam = keras.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)
    model.compile(loss='categorical_crossentropy', metrics=['accuracy'], optimizer=adam)
    plot_model(model, to_file='model.png', show_shapes=True)  # print model
    print('models layers:', model.layers)
    print('models config:', model.get_config())
    print('models summary:', model.summary())
