# -*- coding: utf-8 -*-
"""
Medicare Image Classification
Dual tree complex wavelet transform based CNN by using keras modular in 2-Dimension.
Compared Trandional and dual-tree complex wavelet transform based on CNN.

Models:
Model 1 - trandional CNN.
Model 2 - dual-tree complex wavelet transform, a dual-tree wavelet pooling layer is concatenated to the traditional pooling layers.

Inputs:
batch_size - size of batching thousands of patches from a medicare image.
num_classes - # of classes.
epochs - # of epochs.
img_rows, img_cols - size of image.

Functions:
waveletpool2d - perform a forward dtwct transform on an image with multiple data format, e.g., nhwc - batch of images with channel dimension
                  as the last dimension, Batch dimension is first.
wlcc - concatenated dual - tree wavelet pooling layer with the traditional pooling layers in a CNN.
compare_cnn - compare two models.
q2c - convert from quads in y to complex numbers in z.
c2q - scale by gain and convert from complex w(:,:,1:2) to real quad-numbers in z.

Created on Wed Apr 11 14:59:33 2018
@author: Hongya Lu
"""

from __future__ import print_function
import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K

from keras.layers import Input, merge, Dropout, Dense, Flatten, Activation
from keras.layers.convolutional import MaxPooling2D, Convolution2D, AveragePooling2D
from keras.layers.normalization import BatchNormalization
from keras.models import Model
from keras.layers import Concatenate
from keras import backend as K
from keras.utils.data_utils import get_file

from keras.layers import Lambda
from keras.optimizers import SGD, Adam
import dtcwt

batch_size = 128
num_classes = 10
epochs = 12
print(epochs)
# input image dimensions
img_rows, img_cols = 28,28

# the data, shuffled and SPLIT between train and test sets
( X_train, y_train ), ( X_test, y_test ) = mnist.load_data()


if K.image_data_format() == 'channels_first':
    X_train = X_train.reshape( X_train.shape[0], 1, img_rows, img_cols )
    X_test = X_test.reshape( X_test.shape[0], 1, img_rows, img_cols )
    input_shape = ( 1, img_rows, img_cols )
else:
    X_train = X_train.reshape( X_train.shape[0], img_rows, img_cols, 1 )
    X_test = X_test.reshape( X_test.shape[0], img_rows, img_cols, 1 )
    input_shape = ( img_rows, img_cols, 1 )

X_train = X_train.astype( 'float32' )
X_test = X_test.astype( 'float32' )
X_train /= 255
X_test /= 255
print( 'X_train shape:', X_train.shape )
print( X_train.shape[0], 'train samples' )
print( X_test.shape[0], 'test samples' )

# convert class vectors to binary class matrices
Y_train = keras.utils.to_categorical( y_train, num_classes )
Y_test = keras.utils.to_categorical( y_test, num_classes )


def waveletpool2d( x ):
    xshape = x.get_shape().as_list()
    trans = Transform2d( biort = 'near_sym_b', qshift = 'qshift_b')
  #  y = tf.transpose( x, perm = [0,3,1,2] )
    y1 = trans.forward_channels( x, nlevels = 2, data_format = 'nhwc', include_scale = 'True' )
    y1 = y1.lowpass_op
#    yshape = y1.get_shape().as_list()
#    y = tf.transpose( x,perm=[0,3,1,2] )
#    y2 = tf.reshape( tensor = y1, shape = ( -1, xshape[1], yshape[1], yshape[2], yshape[3] ) )
    return y1

mywl2d = Lambda( lambda x: waveletpool2d(x) )


# Create model1, Traditional Model
model = Sequential()
model.add( Conv2D( 32, ( 2, 2 ), padding = 'same’, input_shape = X_train.shape[1:] ) )
model.add( Activation( 'relu' ) )
model.add( mywl2d )
model.add( Conv2D( 32, ( 2, 2 ), padding = 'same' ) )
model.add( Activation( 'relu' ) )
model.add( mywl2d )
model.add( Conv2D( 64, ( 3, 3 ), padding = 'valid' ) )
model.add( Activation( 'relu' ) )
model.add( Dropout( 0.5 ) )
model.add( Conv2D( 64, ( 3, 3 ), padding = 'valid' ) )
model.add( Activation( 'relu' ) )
model.add( Dropout( 0.5 ) )
model.add( Dropout( 0.5 ) )
model.add( Flatten() )
model.add( Dense( 512 ) )
model.add( Activation( 'relu' ) )
model.add( Dropout( 0.5 ) )
model.add( Dense( num_classes ) )
model.add( Activation( 'softmax' ) )

model.compile( loss = 'categorical_crossentropy', optimizer = 'adam', metrics = ['accuracy'] )
model.summary()

model.fit( X_train, Y_train, batch_size = batch_size, epochs = epochs, verbose = 1, validation_data = ( X_test, Y_test ) )
score = model.evaluate( X_test, Y_test, verbose = 0 )
print( 'Test loss:', score[0] )
print( 'Test accuracy:', score[1] )

# concatenate (b) and (c)
def wlcc( input_shape, nb_classes = 3 ):
    '''
    Creates a inception v4 network

    :param nb_classes: number of classes.txt
    :return: Keras Model with 1 input and 1 output
    '''
    if K.image_dim_ordering() == ‘th’:
        channel_axis = 1
    else:
        channel_axis = -1  # channels_last is default in Keras
    init = Input(input_shape)
    x =  Conv2D( 32, kernel_size = ( 3, 3 ), strides = ( 1, 1 ), activation = 'relu', padding = 'same', input_shape = input_shape )( init )
 #   x2 = lzwl( init )
    x2 = mywl2d( x )
    x =  Conv2D( 64, kernel_size = ( 3, 3 ), activation = 'relu', padding = 'same', input_shape = input_shape )( x )
    x1 = Conv2D( 64, ( 2,2 ), strides = ( 2, 2 ), activation = 'relu', padding = 'valid' )( x )
    # Input Shape is 299 x 299 x 3 (tf) or 3 x 299 x 299 (th
    branches = [ x1, x2 ]
    x = Concatenate( axis = channel_axis )( branches )   
    x3 = Conv2D( 96, ( 2, 2 ), strides = ( 2, 2 ), activation = 'relu', padding = 'valid' )( x )
    # Input Shape is 299 x 299 x 3 (tf) or 3 x 299 x 299 (th)
    x4 = mywl2d( x2 )
    branches = [ x3, x4 ]
    x = Concatenate( axis = channel_axis )( branches )   
    x = Conv2D( 128, ( 2, 2 ), strides = ( 2, 2 ), activation = 'relu', padding = 'valid' )( x )
#    x6 = mywl2d( x4 )
#    branches = [ x, x6 ]
 #   x = Concatenate( axis = channel_axis )( branches ) 
    x = AveragePooling2D( ( 2, 2 ), strides = ( 1, 1 ), padding = 'same' )( x )
    # Dropout
    x = Dropout( 0.5 )( x )
    x = Flatten()( x )
    x = Dense( activation = 'relu', units = 512 )( x )
    x = Dropout( 0.5 )( x )
    # Output
    out = Dense( activation = 'softmax', units = nb_classes )( x )
    model = Model( init, out, name = 'wlcc' )
    return model

# Model 2, the dtcwt pooling layer is concatenated to the traditional pooling layers 
batch_size = 100
epochs = 200
model = Sequential()
model = wlcc( input_shape = input_shape )
model.compile( loss = 'categorical_crossentropy', optimizer = 'adam', metrics=[ 'accuracy' ] )
model.summary()

model.fit( X_train, Y_train, batch_size = batch_size, epochs = epochs, verbose = 1, validation_data = ( X_test, Y_test ) )
score = model.evaluate( X_test, Y_test, verbose = 0 )
print( 'Test loss:', score[0] )
print( 'Test accuracy:', score[1] )


##### compare structure:testing 73.05 %
def compare_cnn( input_shape, nb_classes = 10 ):
    '''
    Creates a inception v4 network

    :param nb_classes: number of classes.txt
    :return: Keras Model with 1 input and 1 output
    '''
    if K.image_dim_ordering() == ‘th’:
        channel_axis = 1
    else:
        channel_axis = -1  # channels_last is default in Keras
    init = Input( input_shape )
    x =  Conv2D( 32, kernel_size = ( 3, 3 ), activation = 'relu', padding = 'same', input_shape = input_shape )( init )
    x =  Conv2D( 64, kernel_size=( 3, 3 ), activation = 'relu', padding = 'same', input_shape = input_shape )( x )
    x = Conv2D( 64, ( 2, 2 ), strides = ( 2, 2 ), activation = 'relu', padding = 'valid' )( x )
    # Input Shape is 299 x 299 x 3 (tf) or 3 x 299 x 299 (th)
#    x2 = mywl2d( x )
#    branches = [ x1, x2 ]
#    x = Concatenate( axis = channel_axis )( branches )   
    x = Conv2D( 96, ( 2, 2 ), strides = ( 2, 2 ), activation = 'relu', padding = 'valid' )( x )
    x = Conv2D( 128, ( 2, 2 ), strides = ( 2, 2 ), activation = 'relu', padding = 'valid' )( x )
    x = AveragePooling2D( ( 2, 2 ), strides = ( 1, 1 ), padding = 'same' )( x )
    x = Dropout( 0.5 )( x )
    x = Flatten()( x )
    x = Dense( activation = 'relu', units = 512 )( x )
    x = Dropout( 0.5 )( x )
    # Output
    out = Dense( activation = 'softmax', units = nb_classes )( x )
    model = Model( init, out, name = 'compare' )
    return model


batch_size = 100
epochs = 100
model = Sequential()
model = compare_cnn( input_shape = input_shape )
model.compile( loss = 'categorical_crossentropy', optimizer = 'adam', metrics = [ 'accuracy' ] )
model.summary()

model.fit( X_train, Y_train, batch_size = batch_size, epochs = epochs, verbose = 1, validation_data = ( X_test, Y_test ) )
score = model.evaluate( X_test, Y_test, verbose = 0 )
print( 'Test loss:', score[0] )
print( 'Test accuracy:', score[1] )



# basic dtcwt functions


from __future__ import absolute_import

import numpy as np
import logging

from six.moves import xrange

from dtcwt.coeffs import biort as _biort, qshift as _qshift
from dtcwt.defaults import DEFAULT_BIORT, DEFAULT_QSHIFT
from dtcwt.utils import asfarray
from dtcwt.tf import Pyramid
from dtcwt.numpy import Pyramid as Pyramid_np

from dtcwt.tf.lowlevel import coldfilt, rowdfilt, rowfilter, colfilter, colifilt

try:
    import tensorflow as tf
    from tensorflow.python.framework import dtypes
    tf_dtypes = frozenset(
        [dtypes.float32, dtypes.float64, dtypes.int8, dtypes.int16,
         dtypes.int32, dtypes.int64, dtypes.uint8, dtypes.qint8, dtypes.qint32,
         dtypes.quint8, dtypes.complex64, dtypes.complex128,
         dtypes.float32_ref, dtypes.float64_ref, dtypes.int8_ref,
         dtypes.int16_ref, dtypes.int32_ref, dtypes.int64_ref, dtypes.uint8_ref,
         dtypes.qint8_ref, dtypes.qint32_ref, dtypes.quint8_ref,
         dtypes.complex64_ref, dtypes.complex128_ref]
    )
except ImportError:
    # The lack of tensorflow will be caught by the low-level routines.
    pass

np_dtypes = frozenset(
    [np.dtype('float16'), np.dtype('float32'), np.dtype('float64'),
     np.dtype('int8'), np.dtype('int16'), np.dtype('int32'),
     np.dtype('int64'), np.dtype('uint8'), np.dtype('uint16'),
     np.dtype('uint32'), np.dtype('complex64'), np.dtype('complex128')]
)


class Transform2d(object):
    """
    An implementation of the 2D DT-CWT via Tensorflow.

    :param biort: The biorthogonal wavelet family to use.
    :param qshift: The quarter shift wavelet family to use.

    .. note::

        *biort* and *qshift* are the wavelets which parameterise the transform.
        If *biort* or *qshift* are strings, they are used as an argument to the
        :py:func:`dtcwt.coeffs.biort` or :py:func:`dtcwt.coeffs.qshift`
        functions.  Otherwise, they are interpreted as tuples of vectors giving
        filter coefficients. In the *biort* case, this should be (h0o, g0o, h1o,
        g1o). In the *qshift* case, this should be (h0a, h0b, g0a, g0b, h1a,
        h1b, g1a, g1b).

    .. note::

        Calling the methods in this class with different inputs will slightly
        vary the results. If you call the
        :py:meth:`~dtcwt.tf.Transform2d.forward` or
        :py:meth:`~dtcwt.tf.Transform2d.forward_channels` methods with a numpy
        array, they load this array into a :py:class:`tf.Variable` and create
        the graph. Subsequent calls to :py:attr:`dtcwt.tf.Pyramid.lowpass` or
        other attributes in the pyramid will create a session and evaluate these
        parameters.  If the above methods are called with a tensorflow variable
        or placeholder, these will be used to create the graph. As such, to
        evaluate the results, you will need to look at the
        :py:attr:`dtcwt.tf.Pyramid.lowpass_op` attribute (calling the `lowpass`
        attribute will try to evaluate the graph with no initialized variables
        and likely result in a runtime error).

        The behaviour is similar for the inverse methods, except these return an
        array, rather than a Pyramid style class. If a
        :py:class:`dtcwt.tf.Pyramid` was created by calling the forward methods
        with a numpy array, providing this pyramid to the inverse methods will
        return a numpy array. If however a :py:class:`dtcwt.tf.Pyramid` was
        created by calling the forward methods with a tensorflow variable, the
        result from calling the inverse methods will also be a tensorflow
        variable.

    .. codeauthor:: Fergal Cotter <fbc23@cam.ac.uk>, Feb 2017
    .. codeauthor:: Rich Wareham <rjw57@cantab.net>, Aug 2013
    .. codeauthor:: Nick Kingsbury, Cambridge University, Sept 2001
    .. codeauthor:: Cian Shaffrey, Cambridge University, Sept 2001
    """

    def __init__(self, biort=DEFAULT_BIORT, qshift=DEFAULT_QSHIFT):
        try:
            self.biort = _biort(biort)
        except TypeError:
            self.biort = biort

        # Load quarter sample shift wavelets
        try:
            self.qshift = _qshift(qshift)
        except TypeError:
            self.qshift = qshift

    def forward(self, X, nlevels=3, include_scale=False):
        """ Perform a forward transform on an image.

        Can provide the forward transform with either an np array (naive
        usage), or a tensorflow variable or placeholder (designed usage). To
        transform batches of images, use the :py:meth:`forward_channels` method.

        :param ndarray X: Input image which you wish to transform. Can be a
            numpy array, tensorflow Variable or tensorflow placeholder. See
            comments below.
        :param int nlevels: Number of levels of the dtcwt transform to
            calculate.
        :param bool include_scale: Whether or not to return the lowpass results
            at each scale of the transform, or only at the highest scale (as is
            custom for multi-resolution analysis)

        :returns: A :py:class:`dtcwt.tf.Pyramid` object

        .. note::

            If a numpy array is provided, the forward function will create a
            tensorflow variable to hold the input image, and then create the
            graph of the right size to match the input, and then feed the
            input into the graph and evaluate it.  This operation will
            return a :py:class:`Pyramid` object similar to how running
            the numpy version would.

        .. codeauthor:: Fergal Cotter <fbc23@cam.ac.uk>, Feb 2017
        .. codeauthor:: Rich Wareham <rjw57@cantab.net>, Aug 2013
        .. codeauthor:: Nick Kingsbury, Cambridge University, Sept 2001
        .. codeauthor:: Cian Shaffrey, Cambridge University, Sept 2001
        """

        # Check if a numpy array was provided
        numpy = False
        try:
            dtype = X.dtype
        except AttributeError:
            X = asfarray(X)
            dtype = X.dtype

        if dtype in np_dtypes:
            numpy = True
            X = np.atleast_2d(X)
            X = tf.Variable(X, dtype=tf.float32, trainable=False)

        if X.dtype not in tf_dtypes:
            raise ValueError('I cannot handle the variable you have ' +
                             'provided of type ' + str(X.dtype) + '. ' +
                             'Inputs should be a numpy or tf array')

        X_shape = tuple(X.get_shape().as_list())
        if len(X_shape) == 2:
            # Need to make it a batch for tensorflow
            X = tf.expand_dims(X, axis=0)
        elif len(X_shape) >= 3:
            raise ValueError(
                'The entered variable has too many ' +
                'dimensions - ' + str(X_shape) + '. For batches of ' +
                'images with multiple channels (i.e. 3 or 4 dimensions), ' +
                'please either enter each channel separately, or use ' +
                'the forward_channels method.')

        X_shape = tuple(X.get_shape().as_list())
        original_size = X_shape[1:]
        size = '{}x{}'.format(original_size[0], original_size[1])
        name = 'dtcwt_fwd_{}'.format(size)
        with tf.variable_scope(name):
            Yl, Yh, Yscale = self._forward_ops(X, nlevels)

        Yl = Yl[0]
        Yh = tuple(x[0] for x in Yh)
        Yscale = tuple(x[0] for x in Yscale)

        if include_scale:
            return Pyramid(Yl, Yh, Yscale, numpy)
        else:
            return Pyramid(Yl, Yh, None, numpy)

    def forward_channels(self, X, data_format, nlevels=3,
                         include_scale=False):
        """ Perform a forward transform on an image with multiple channels.

        Will perform the DTCWT independently on each channel.

        :param X: Input image which you wish to transform.
        :param int nlevels: Number of levels of the dtcwt transform to
            calculate.
        :param bool include_scale: Whether or not to return the lowpass results
            at each scale of the transform, or only at the highest scale (as is
            custom for multiresolution analysis)
        :param str data_format: An optional string of the form:
            "nhw" (or "chw"), "hwn" (or "hwc"), "nchw" or "nhwc". Note that for
            these strings, 'n' is used to indicate where the batch dimension is,
            'c' is used to indicate where the image channels are, 'h' is used to
            indicate where the row dimension is, and 'c' is used to indicate
            where the columns are. If the data_format is:

                - "nhw" : the input will be interpreted as a batch of 2D images,
                  with the batch dimension as the first.
                - "chw" : will function exactly the same as "nhw" but is offered
                  to indicate the input is a 2D image with channels.
                - "hwn" : the input will be interpreted as a batch of 2D images
                  with the batch dimension as the last.
                - "hwc" : will function exatly the same as "hwc" but is offered
                  to indicate the input is a 2D image with channels.
                - "nchw" : the input is a batch of images with channel dimension
                  as the second dimension. Batch dimension is first.
                - "nhwc" : the input is a batch of images with channel dimension
                  as the last dimension. Batch dimension is first.

        :returns: A :py:class:`dtcwt.tf.Pyramid` object

        .. codeauthor:: Fergal Cotter <fbc23@cam.ac.uk>, Feb 2017
        .. codeauthor:: Rich Wareham <rjw57@cantab.net>, Aug 2013
        .. codeauthor:: Nick Kingsbury, Cambridge University, Sept 2001
        .. codeauthor:: Cian Shaffrey, Cambridge University, Sept 2001
        """
        data_format = data_format.lower()
        formats_3d = ("nhw", "chw", "hwn", "hwc")
        formats_4d = ("nchw", "nhwc")
        formats = formats_3d + formats_4d
        if data_format not in formats:
            raise ValueError('The data format must be one of: {}'.
                             format(formats))

        try:
            dtype = X.dtype
        except AttributeError:
            X = asfarray(X)
            dtype = X.dtype

        numpy = False
        if dtype in np_dtypes:
            numpy = True
            X = np.atleast_2d(X)
            X = tf.Variable(X, dtype=tf.float32, trainable=False)

        if X.dtype not in tf_dtypes:
            raise ValueError('I cannot handle the variable you have ' +
                             'provided of type ' + str(X.dtype) + '. ' +
                             'Inputs should be a numpy or tf array.')

        X_shape = X.get_shape().as_list()

        # if not ((len(X_shape) == 3 and data_format in formats_3d) or
        #         (len(X_shape) == 4 and data_format in formats_4d)):
        #     raise ValueError(
        #         'The entered variable has incorrect shape - ' +
        #         str(X_shape) + ' for the specified data_format ' +
        #         data_format + '.')

        # Reshape the inputs to all be 3d inputs of shape (batch, h, w)
        if data_format in formats_4d:
            # Move all of the channels into the batch dimension for the
            # input.  This may involve transposing, depending on the data
            # format
            with tf.variable_scope('ch_to_batch'):
                s = X.get_shape().as_list()[1:]
                size = '{}x{}'.format(s[0], s[1])
                name = 'dtcwt_fwd_{}'.format(size)
                if data_format == 'nhwc':
                    nch = s[2]
                    X = tf.transpose(X, perm=[0, 3, 1, 2])
                    X = tf.reshape(X, [-1, s[0], s[1]])
                else:
                    nch = s[0]
                    X = tf.reshape(X, [-1, s[1], s[2]])
        elif data_format == "hwn" or data_format == "hwc":
            s = X.get_shape().as_list()[:2]
            size = '{}x{}'.format(s[0], s[1])
            name = 'dtcwt_fwd_{}'.format(size)
            with tf.variable_scope('ch_to_start'):
                X = tf.transpose(X, perm=[2,0,1])
        else:
            s = X.get_shape().as_list()[1:3]
            size = '{}x{}'.format(s[0], s[1])
            name = 'dtcwt_fwd_{}'.format(size)

        # Do the dtcwt, now with a 3 dimensional input
        with tf.variable_scope(name):
            Yl, Yh, Yscale = self._forward_ops(X, nlevels)

        # Reshape it all again to match the input
        if data_format in formats_4d:
            # Put the channels back into their correct positions
            with tf.variable_scope('batch_to_ch'):
                # Reshape Yl
                s = Yl.get_shape().as_list()[1:]
                Yl = tf.reshape(Yl, [-1, nch, s[0], s[1]], name='Yl_reshape')
                if data_format == 'nhwc':
                    Yl = tf.transpose(Yl, [0, 2, 3, 1], name='Yl_ch_to_end')

                # Reshape Yh
                with tf.variable_scope('Yh'):
                    Yh_new = [None,] * nlevels
                    for i in range(nlevels):
                        s = Yh[i].get_shape().as_list()[1:]
                        Yh_new[i] = tf.reshape(
                            Yh[i], [-1, nch, s[0], s[1], s[2]],
                            name='scale{}_reshape'.format(i))
                        if data_format == 'nhwc':
                            Yh_new[i] = tf.transpose(
                                Yh_new[i], [0, 2, 3, 1, 4],
                                name='scale{}_ch_to_end'.format(i))
                    Yh = tuple(Yh_new)

                # Reshape Yscale
                if include_scale:
                    with tf.variable_scope('Yscale'):
                        Yscale_new = [None,] * nlevels
                        for i in range(nlevels):
                            s = Yscale[i].get_shape().as_list()[1:]
                            Yscale_new[i] = tf.reshape(
                                Yscale[i], [-1, nch, s[0], s[1]],
                                name='scale{}_reshape'.format(i))
                            if data_format == 'nhwc':
                                Yscale_new[i] = tf.transpose(
                                    Yscale_new[i], [0, 2, 3, 1],
                                    name='scale{}_ch_to_end'.format(i))
                        Yscale = tuple(Yscale_new)

        elif data_format == "hwn" or data_format == "hwc":
            with tf.variable_scope('ch_to_end'):
                Yl = tf.transpose(Yl, perm=[1,2,0], name='Yl')
                Yh = tuple(
                    tf.transpose(x, [1, 2, 0, 3], name='Yh{}'.format(i))
                    for i,x in enumerate(Yh))
                if include_scale:
                    Yscale = tuple(
                        tf.transpose(x, [1, 2, 0], name='Yscale{}'.format(i))
                        for i,x in enumerate(Yscale))

        # Return the pyramid
        if include_scale:
            return Pyramid(Yl, Yh, Yscale, numpy)
        else:
            return Pyramid(Yl, Yh, None, numpy)

    def inverse(self, pyramid, gain_mask=None):
        """ Perform an inverse transform on an image.

        Can provide the inverse transform with either an np array (naive
        usage), or a tensorflow variable or placeholder (designed usage).

        :param pyramid: A :py:class:`dtcwt.tf.Pyramid` like class holding
            the transform domain representation to invert
        :param gain_mask: Gain to be applied to each sub-band. Should have shape
            (6, nlevels) or be None.

        :returns: An array , X, compatible with the reconstruction. Will be a tf
            Variable if the Pyramid was made with tf inputs, otherwise a numpy
            array.

        .. note::

            A tf.Variable is returned if the pyramid input was a Pyramid class.
            If it wasn't, then, we return a numpy array (note that this is
            inefficient, as in both cases we have to construct the graph - in
            the second case, we then execute it and discard it).

        The (*d*, *l*)-th element of *gain_mask* is gain for subband with
        direction *d* at level *l*. If gain_mask[d,l] == 0, no computation is
        performed for band (d,l). Default *gain_mask* is all ones. Note that
        both *d* and *l* are zero-indexed.

        .. codeauthor:: Fergal Cotter <fbc23@cam.ac.uk>, Feb 2017
        .. codeauthor:: Rich Wareham <rjw57@cantab.net>, Aug 2013
        .. codeauthor:: Nick Kingsbury, Cambridge University, Sept 2001
        .. codeauthor:: Cian Shaffrey, Cambridge University, Sept 2001
        """

        # A tensorflow object was provided
        numpy = False
        if isinstance(pyramid, Pyramid):
            Yl = pyramid.lowpass_op
            Yh = pyramid.highpasses_ops
            numpy = pyramid.numpy

        # Check if a numpy pyramid was provided
        elif isinstance(pyramid, Pyramid_np) or \
                hasattr(pyramid, 'lowpass') and hasattr(pyramid, 'highpasses'):
            numpy = True
            Yl, Yh = pyramid.lowpass, pyramid.highpasses
            Yl = tf.Variable(Yl, trainable=False, dtype=tf.float32)
            Yh = tuple(
                tf.Variable(level, trainable=False, dtype=tf.complex64)
                for level in Yh)
        else:
            raise ValueError(
                'Unknown pyramid provided to inverse transform')

        # Need to make sure it has at least 3 dimensions for tensorflow
        Yl_shape = tuple(Yl.get_shape().as_list())
        if len(Yl_shape) == 2:
            Yl = tf.expand_dims(Yl, axis=0)
            Yh = tuple(tf.expand_dims(x, axis=0) for x in Yh)
        elif len(Yl_shape) >= 3:
            raise ValueError(
                'The entered variables have too many ' +
                'dimensions - ' + str(Yl_shape) + '. For batches of ' +
                'images with multiple channels (i.e. 3 or 4 dimensions), ' +
                'please either enter each channel separately, or use ' +
                'the inverse_channels method.')

        # Do the inverse transform
        s = Yl.get_shape().as_list()[1:]
        nlevels = len(Yh)
        size = '{}x{}_up_{}'.format(s[0], s[1], nlevels)
        name = 'dtcwt_inv_{}'.format(size)
        with tf.variable_scope(name):
            X = self._inverse_ops(Yl, Yh, gain_mask)

        # Chop off the first dimension
        X = X[0]

        if numpy:
            with tf.Session() as sess:
                sess.run(tf.global_variables_initializer())
                X = sess.run(X)

        return X

    def inverse_channels(self, pyramid, data_format, gain_mask=None):
        """
        Perform an inverse transform on an image with multiple channels.

        Must provide with a tensorflow variable or placeholder (unlike the more
        general :py:meth:`~dtcwt.tf.Transform2d.inverse`).

        This is designed to work after calling the
        :py:meth:`~dtcwt.tf.Transform2d.forward_channels` method. You must use
        the same data_format for the inverse_channels as the one used for the
        forward_channels (unless you have explicitly reshaped the output).

        :param pyramid: A :py:class:`dtcwt.tf.Pyramid` like class holding
            the transform domain representation to invert
        :param str data_format: An optional string of the form:
            "nhw" (or "chw"), "hwn" (or "hwc"), "nchw" or "nhwc". Note that for
            these strings, 'n' is used to indicate where the batch dimension is,
            'c' is used to indicate where the image channels are, 'h' is used to
            indicate where the row dimension is, and 'c' is used to indicate
            where the columns are. If the data_format is::

                * "nhw" - the input will be interpreted as a batch of 2D images,
                  with the batch dimension as the first.
                * "chw" - will function exactly the same as "nhw" but it offered
                  to indicate the input is a 2D image with channels.
                * "hwn" - the input will be interpreted as a batch of 2D images
                  with the batch dimension as the last.
                * "hwc" - will function exatly the same as "hwc" but is offered
                  to indicate the input is a 2D image with channels.
                * "nchw" - the input is a batch of images with channel dimension
                  as the second dimension. Batch dimension is first.
                * "nhwc" - the input is a batch of images with channel dimension
                  as the last dimension. Batch dimension is first.

        :param gain_mask: Gain to be applied to each subband. Should have shape
            [6, nlevels].

        :returns: An array , X, compatible with the reconstruction. Will be a tf
            Variable if the Pyramid was made with tf inputs, otherwise a numpy
            array.


        The (*d*, *l*)-th element of *gain_mask* is gain for subband with
        direction *d* at level *l*. If gain_mask[d,l] == 0, no computation is
        performed for band (d,l). Default *gain_mask* is all ones. Note that
        both *d* and *l* are zero-indexed.

        .. codeauthor:: Fergal Cotter <fbc23@cam.ac.uk>, Feb 2017
        .. codeauthor:: Rich Wareham <rjw57@cantab.net>, Aug 2013
        .. codeauthor:: Nick Kingsbury, Cambridge University, Sept 2001
        .. codeauthor:: Cian Shaffrey, Cambridge University, Sept 2001
        """
        # Input checking
        data_format = data_format.lower()
        formats_3d = ("nhw", "chw", "hwn", "hwc")
        formats_4d = ("nchw", "nhwc")
        formats = formats_3d + formats_4d
        if data_format not in formats:
            raise ValueError('The data format must be one of: {}'.
                             format(formats))

        # A tensorflow object was provided
        numpy = False
        if isinstance(pyramid, Pyramid):
            Yl = pyramid.lowpass_op
            Yh = pyramid.highpasses_ops
            numpy = pyramid.numpy

        # Check if a numpy pyramid was provided
        elif isinstance(pyramid, Pyramid_np) or \
                hasattr(pyramid, 'lowpass') and hasattr(pyramid, 'highpasses'):
            numpy = True
            Yl, Yh = pyramid.lowpass, pyramid.highpasses
            Yl = tf.Variable(Yl, trainable=False, dtype=tf.float32)
            Yh = tuple(
                tf.Variable(level, trainable=False, dtype=tf.complex64)
                for level in Yh)
        else:
            raise ValueError(
                'Unknown pyramid provided to inverse transform')

        # Check the shape was correct
        Yl_shape = Yl.get_shape().as_list()
        if not ((len(Yl_shape) == 3 and data_format in formats_3d) or
                (len(Yl_shape) == 4 and data_format in formats_4d)):
            raise ValueError(
                'The entered variable has incorrect shape - ' +
                str(Yl_shape) + ' for the specified data_format ' +
                data_format + '.')

        # Reshape the inputs to all be 3d inputs of shape (batch, h, w)
        if data_format in formats_4d:
            if data_format == "nhwc":
                channel_ax = 3
            else:
                channel_ax = 1
            # Move all of the channels into the batch dimension for the lowpass
            # input. This may involve transposing, depending on the data format
            with tf.variable_scope('ch_to_batch'):
                s = Yl.get_shape().as_list()
                num_channels = s[channel_ax]
                nlevels = len(Yh)
                if data_format == "nhwc":
                    size = '{}x{}_up_{}'.format(s[1], s[2], nlevels)
                    Yl = tf.transpose(Yl, [0, 3, 1, 2])
                    Yl = tf.reshape(Yl, [-1, s[1], s[2]])
                else:
                    size = '{}x{}_up_{}'.format(s[2], s[3], nlevels)
                    Yl = tf.reshape(Yl, [-1, s[2], s[3]])

                # Move all of the channels into the batch dimension for the
                # highpass input. This may involve transposing, depending on the
                # data format
                Yh_new = []
                for scale in Yh:
                    s = scale.get_shape().as_list()
                    if s[channel_ax] != num_channels:
                        raise ValueError(
                            """The number of channels has to be consistent for all
                            inputs across the channel axis {}. You fed in Yl: {}
                            and Yh: {}""".format(channel_ax, Yl, Yh))
                    if data_format == "nhwc":
                        scale = tf.transpose(scale, [0, 3, 1, 2, 4])
                        Yh_new.append(tf.reshape(scale, [-1, s[1], s[2], s[4]]))
                    else:
                        Yh_new.append(tf.reshape(scale, [-1, s[2], s[3], s[4]]))
                Yh = Yh_new

        elif data_format == "hwn" or data_format == "hwc":
            s = Yl.get_shape().as_list()
            num_channels = s[2]
            size = '{}x{}'.format(s[0], s[1])
            with tf.variable_scope('ch_to_start'):
                Yl = tf.transpose(Yl, perm=[2,0,1], name='Yl')
                Yh = tuple(
                    tf.transpose(x, [2, 0, 1, 3], name='Yh{}'.format(i))
                    for i,x in enumerate(Yh))

        else:
            s = Yl.get_shape().as_list()
            size = '{}x{}'.format(s[1], s[2])
            num_channels = s[0]

        # Do the inverse dtcwt, now with the same shape input
        name = 'dtcwt_inv_{}_{}channels'.format(size, num_channels)
        with tf.variable_scope(name):
            X = self._inverse_ops(Yl, Yh, gain_mask)

        # Reshape the output to match the input shape.
        if data_format in formats_4d:
            with tf.variable_scope('batch_to_ch'):
                s = X.get_shape().as_list()
                X = tf.reshape(X, [-1, num_channels, s[1], s[2]])
                if data_format == "nhwc":
                    X = tf.transpose(X, [0, 2, 3, 1], name='X')
        else:
            if data_format == "hwn" or data_format == "hwc":
                with tf.variable_scope('ch_to_end'):
                    X = tf.transpose(X, [1, 2, 0], name="X")

        # If the user expects numpy back, evaluate the data.
        if numpy:
            with tf.Session() as sess:
                sess.run(tf.global_variables_initializer())
                X = sess.run(X)

        return X

    def _forward_ops(self, X, nlevels=3):
        """ Perform a *n*-level DTCWT-2D decompostion on a 2D matrix *X*.

        :param X: 3D real array of size [batch, h, w]
        :param nlevels: Number of levels of wavelet decomposition
        :param extended: True if a singleton dimension was added at the
            beginning of the input. Signal to remove afterwards.

        :returns: A tuple of Yl, Yh, Yscale
        """

        # If biort has 6 elements instead of 4, then it's a modified
        # rotationally symmetric wavelet
        # FIXME: there's probably a nicer way to do this
        if len(self.biort) == 4:
            h0o, g0o, h1o, g1o = self.biort
        elif len(self.biort) == 6:
            h0o, g0o, h1o, g1o, h2o, g2o = self.biort
        else:
            raise ValueError('Biort wavelet must have 6 or 4 components.')

        # If qshift has 12 elements instead of 8, then it's a modified
        # rotationally symmetric wavelet
        # FIXME: there's probably a nicer way to do this
        if len(self.qshift) == 8:
            h0a, h0b, g0a, g0b, h1a, h1b, g1a, g1b = self.qshift
        elif len(self.qshift) == 12:
            h0a, h0b, g0a, g0b, h1a, h1b, g1a, g1b, h2a, h2b = self.qshift[:10]
        else:
            raise ValueError('Qshift wavelet must have 12 or 8 components.')

        # Check the shape and form of the input
        if X.dtype not in tf_dtypes:
            raise ValueError('X needs to be a tf variable or placeholder')

        original_size = X.get_shape().as_list()[1:]



        # ############################ Resize #################################
        # The next few lines of code check to see if the image is odd in size,
        # if so an extra ... row/column will be added to the bottom/right of the
        # image
        initial_row_extend = 0
        initial_col_extend = 0
        # If the row count of X is not divisible by 2 then we need to
        # extend X by adding a row at the bottom
        if original_size[0] % 2 != 0:
            bottom_row = tf.slice(X, [0, original_size[0] - 1, 0], [-1, 1, -1])
            X = tf.concat([X, bottom_row], axis=1)
            initial_row_extend = 1

        # If the col count of X is not divisible by 2 then we need to
        # extend X by adding a col to the right
        if original_size[1] % 2 != 0:
            right_col = tf.slice(X, [0, 0, original_size[1] - 1], [-1, -1, 1])
            X = tf.concat([X, right_col], axis=2)
            initial_col_extend = 1

        extended_size = X.get_shape().as_list()[1:3]

        if nlevels == 0:
            return X, (), ()

        # ########################### Initialise ###############################
        Yh = [None, ] * nlevels
        # This is only required if the user specifies a third output
        # component.
        Yscale = [None, ] * nlevels

        # ############################ Level 1 #################################
        # Uses the biorthogonal filters
        if nlevels >= 1:
            # Do odd top-level filters on cols.
            Lo = colfilter(X, h0o)
            Hi = colfilter(X, h1o)
            if len(self.biort) >= 6:
                Ba = colfilter(X, h2o)

            # Do odd top-level filters on rows.
            LoLo = rowfilter(Lo, h0o)
            LoLo_shape = LoLo.get_shape().as_list()[1:]

            # Horizontal wavelet pair (15 & 165 degrees)
            horiz = q2c(rowfilter(Hi, h0o))

            # Vertical wavelet pair (75 & 105 degrees)
            vertic = q2c(rowfilter(Lo, h1o))

            # Diagonal wavelet pair (45 & 135 degrees)
            if len(self.biort) >= 6:
                diag = q2c(rowfilter(Ba, h2o))
            else:
                diag = q2c(rowfilter(Hi, h1o))

            # Pack all 6 tensors into one
            Yh[0] = tf.stack(
                [horiz[0], diag[0], vertic[0], vertic[1], diag[1], horiz[1]],
                axis=3)

            Yscale[0] = LoLo

        # ############################ Level 2+ ################################
        # Uses the qshift filters
        for level in xrange(1, nlevels):
            row_size, col_size = LoLo_shape[0], LoLo_shape[1]
            # If the row count of LoLo is not divisible by 4 (it will be
            # divisible by 2), add 2 extra rows to make it so
            if row_size % 4 != 0:
                LoLo = tf.pad(LoLo, [[0, 0], [1, 1], [0, 0]], 'SYMMETRIC')

            # If the col count of LoLo is not divisible by 4 (it will be
            # divisible by 2), add 2 extra cols to make it so
            if col_size % 4 != 0:
                LoLo = tf.pad(LoLo, [[0, 0], [0, 0], [1, 1]], 'SYMMETRIC')

            # Do even Qshift filters on cols.
            Lo = coldfilt(LoLo, h0b, h0a)
            Hi = coldfilt(LoLo, h1b, h1a)
            if len(self.qshift) >= 12:
                Ba = coldfilt(LoLo, h2b, h2a)

            # Do even Qshift filters on rows.
            LoLo = rowdfilt(Lo, h0b, h0a)
            LoLo_shape = LoLo.get_shape().as_list()[1:3]

            # Horizontal wavelet pair (15 & 165 degrees)
            horiz = q2c(rowdfilt(Hi, h0b, h0a))

            # Vertical wavelet pair (75 & 105 degrees)
            vertic = q2c(rowdfilt(Lo, h1b, h1a))

            # Diagonal wavelet pair (45 & 135 degrees)
            if len(self.qshift) >= 12:
                diag = q2c(rowdfilt(Ba, h2b, h2a))
            else:
                diag = q2c(rowdfilt(Hi, h1b, h1a))

            # Pack all 6 tensors into one
            Yh[level] = tf.stack(
                [horiz[0], diag[0], vertic[0], vertic[1], diag[1], horiz[1]],
                axis=3)

            Yscale[level] = LoLo

        Yl = LoLo

        if initial_row_extend == 1 and initial_col_extend == 1:
            logging.warn('The image entered is now a {0} NOT a {1}.'.format(
                'x'.join(list(str(s) for s in extended_size)),
                'x'.join(list(str(s) for s in original_size))))
            logging.warn(
                """The bottom row and rightmost column have been duplicated,
                prior to decomposition.""")

        if initial_row_extend == 1 and initial_col_extend == 0:
            logging.warn('The image entered is now a {0} NOT a {1}.'.format(
                'x'.join(list(str(s) for s in extended_size)),
                'x'.join(list(str(s) for s in original_size))))
            logging.warn(
                'The bottom row has been duplicated, prior to decomposition.')

        if initial_row_extend == 0 and initial_col_extend == 1:
            logging.warn('The image entered is now a {0} NOT a {1}.'.format(
                'x'.join(list(str(s) for s in extended_size)),
                'x'.join(list(str(s) for s in original_size))))
            logging.warn(
                """The rightmost column has been duplicated, prior to
                decomposition.""")

        return Yl, tuple(Yh), tuple(Yscale)

    def _inverse_ops(self, Yl, Yh, gain_mask=None):
        """Perform an *n*-level dual-tree complex wavelet (DTCWT) 2D
        reconstruction.

        :param Yl: The lowpass output from a forward transform. Should be a
            tensorflow variable.
        :param Yh: The tuple of highpass outputs from a forward transform.
            Should be tensorflow variables.
        :param gain_mask: Gain to be applied to each subband.

        :returns: A tf.Variable holding the output

        The (*d*, *l*)-th element of *gain_mask* is gain for subband with
        direction *d* at level *l*. If gain_mask[d,l] == 0, no computation is
        performed for band (d,l). Default *gain_mask* is all ones. Note that
        both *d* and *l* are zero-indexed.

        .. codeauthor:: Fergal Cotter <fbc23@cam.ac.uk>, Feb 2017
        .. codeauthor:: Rich Wareham <rjw57@cantab.net>, Aug 2013
        .. codeauthor:: Nick Kingsbury, Cambridge University, May 2002
        .. codeauthor:: Cian Shaffrey, Cambridge University, May 2002

        """
        a = len(Yh)  # No of levels.

        if gain_mask is None:
            gain_mask = np.ones((6, a))  # Default gain_mask.

        gain_mask = np.array(gain_mask)

        # If biort has 6 elements instead of 4, then it's a modified
        # rotationally symmetric wavelet
        # FIXME: there's probably a nicer way to do this
        if len(self.biort) == 4:
            h0o, g0o, h1o, g1o = self.biort
        elif len(self.biort) == 6:
            h0o, g0o, h1o, g1o, h2o, g2o = self.biort
        else:
            raise ValueError('Biort wavelet must have 6 or 4 components.')

        # If qshift has 12 elements instead of 8, then it's a modified
        # rotationally symmetric wavelet
        # FIXME: there's probably a nicer way to do this
        if len(self.qshift) == 8:
            h0a, h0b, g0a, g0b, h1a, h1b, g1a, g1b = self.qshift
        elif len(self.qshift) == 12:
            h0a, h0b, g0a, g0b, h1a, h1b, \
                g1a, g1b, h2a, h2b, g2a, g2b = self.qshift
        else:
            raise ValueError('Qshift wavelet must have 12 or 8 components.')

        current_level = a
        Z = Yl

        # This ensures that for level 1 we never do the following
        while current_level >= 2:
            lh = c2q(Yh[current_level - 1][:, :, :, 0:6:5],
                     gain_mask[[0, 5],
                     current_level - 1])
            hl = c2q(Yh[current_level - 1][:, :, :, 2:4:1],
                     gain_mask[[2, 3],
                     current_level - 1])
            hh = c2q(Yh[current_level - 1][:, :, :, 1:5:3],
                     gain_mask[[1, 4],
                     current_level - 1])

            # Do even Qshift filters on columns.
            y1 = colifilt(Z, g0b, g0a) + colifilt(lh, g1b, g1a)

            if len(self.qshift) >= 12:
                y2 = colifilt(hl, g0b, g0a)
                y2bp = colifilt(hh, g2b, g2a)

                # Do even Qshift filters on rows.
                y1T = tf.transpose(y1, perm=[0, 2, 1])
                y2T = tf.transpose(y2, perm=[0, 2, 1])
                y2bpT = tf.transpose(y2bp, perm=[0, 2, 1])
                Z = tf.transpose(
                    colifilt(y1T, g0b, g0a) +
                    colifilt(y2T, g1b, g1a) +
                    colifilt(y2bpT, g2b, g2a),
                    perm=[0, 2, 1])
            else:
                y2 = colifilt(hl, g0b, g0a) + colifilt(hh, g1b, g1a)

                # Do even Qshift filters on rows.
                y1T = tf.transpose(y1, perm=[0, 2, 1])
                y2T = tf.transpose(y2, perm=[0, 2, 1])
                Z = tf.transpose(
                    colifilt(y1T, g0b, g0a) +
                    colifilt(y2T, g1b, g1a),
                    perm=[0, 2, 1])

            # Check size of Z and crop as required
            Z_r, Z_c = Z.get_shape().as_list()[1:3]
            S_r, S_c = Yh[current_level - 2].get_shape().as_list()[1:3]
            # check to see if this result needs to be cropped for the rows
            if Z_r != S_r * 2:
                Z = Z[:, 1:-1, :]
            # check to see if this result needs to be cropped for the cols
            if Z_c != S_c * 2:
                Z = Z[:, :, 1:-1]

            # Assert that the size matches at this stage
            Z_r, Z_c = Z.get_shape().as_list()[1:3]
            if Z_r != S_r * 2 or Z_c != S_c * 2:
                raise ValueError(
                    'Sizes of highpasses {}x{} are not '.format(Z_r, Z_c) +
                    'compatible with {}x{} from next level'.format(S_r, S_c))

            current_level = current_level - 1

        if current_level == 1:
            lh = c2q(Yh[current_level - 1][:, :, :, 0:6:5],
                     gain_mask[[0, 5],
                     current_level - 1])
            hl = c2q(Yh[current_level - 1][:, :, :, 2:4:1],
                     gain_mask[[2, 3],
                     current_level - 1])
            hh = c2q(Yh[current_level - 1][:, :, :, 1:5:3],
                     gain_mask[[1, 4],
                     current_level - 1])

            # Do odd top-level filters on columns.
            y1 = colfilter(Z, g0o) + colfilter(lh, g1o)

            if len(self.biort) >= 6:
                y2 = colfilter(hl, g0o)
                y2bp = colfilter(hh, g2o)

                # Do odd top-level filters on rows.
                Z = rowfilter(y1, g0o) + rowfilter(y2, g1o) + \
                    rowfilter(y2bp, g2o)
            else:
                y2 = colfilter(hl, g0o) + colfilter(hh, g1o)

                # Do odd top-level filters on rows.
                Z = rowfilter(y1, g0o) + rowfilter(y2, g1o)

        return Z


def q2c( y ):
    """
    Convert from quads in y to complex numbers in z.
    """

    # Arrange pixels from the corners of the quads into
    # 2 subimages of alternate real and imag pixels.
    #  a----b
    #  |    |
    #  |    |
    #  c----d
    # Combine ( a, b ) and ( d, c ) to form two complex subimages.
    a, b = y[ :, 0::2, 0::2 ], y[ :, 0::2, 1::2 ]
    c, d = y[ :, 1::2, 0::2 ], y[ :, 1::2, 1::2 ]

    p = tf.complex( a / np.sqrt(2), b / np.sqrt(2) )    # p = ( a + jb ) / sqrt(2)
    q = tf.complex( d / np.sqrt(2), -c / np.sqrt(2) )   # q = ( d - jc ) / sqrt(2)

    # Form the 2 highpasses in z.
    return ( p - q, p + q )


def c2q( w, gain ):
    """
    Scale by gain and convert from complex w( :, :, 1:2 ) to real quad-numbers
    in z.

    Arrange pixels from the real and imag parts of the 2 highpasses
    into 4 separate subimages .
     A----B     Re   Im of w( :, :, 1 )
     |    |
     |    |
     C----D     Re   Im of w( :, :, 2 )

    """

    # Input has shape [batch, r, c, 2]
    r, c = w.get_shape().as_list()[ 1:3 ]

    sc = np.sqrt(0.5) * gain
    P = w[ :, :, :, 0 ] * sc[0] + w[ :, :, :, 1 ] * sc[1]
    Q = w[ :, :, :, 0 ] * sc[0] - w[ :, :, :, 1 ] * sc[1]

    # Recover each of the 4 corners of the quads.
    x1 = tf.real( P )
    x2 = tf.imag( P )
    x3 = tf.imag( Q )
    x4 = -tf.real( Q )

    # Stack 2 inputs of shape [batch, r, c] to [batch, r, 2, c]
    x_rows1 = tf.stack( [ x1, x3 ], axis = -2 )
    # Reshaping interleaves the results
    x_rows1 = tf.reshape( x_rows1, [ -1, 2 * r, c ] )
    # Do the same for the even columns
    x_rows2 = tf.stack( [ x2, x4 ], axis = -2 )
    x_rows2 = tf.reshape( x_rows2, [ -1, 2 * r, c ] )

    # Stack the two [batch, 2*r, c] tensors to [batch, 2*r, c, 2]
    x_cols = tf.stack( [ x_rows1, x_rows2 ], axis = -1 )
    y = tf.reshape( x_cols, [ -1, 2 * r, 2 * c ] )

    return y







