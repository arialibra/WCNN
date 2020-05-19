# WCNN
A novel dual-tree complex wavelet transform based Convolutional Neural Network (WCNN) to perform organ tissue segmentation from medical images.

The CNN is a variant of the traditional neural network by introducing convolution and pooling layers that connect to local neighborhoods around each input. However, in the WCNN formulation, a dual-tree wavelet pooling layer is concatenated to the traditional pooling layers in a CNN ( dt is shown as follow ). The DTCWT model adopts Trees a and b as two branches of filters with the same frequency responses to sample the original data and generate the decomposed signals.

![Image text](https://github.com/arialibra/WCNN/blob/master/IMG-folder/dt.png)

A WCNN architecture is designed in following figure. The DTCWT pooling layer can be concatenated to enhance conventional CNNs.Five levels of convolutions are calculated, with two of the convolutional layers concatenated with a DTCWT pooling layer (WP1 and WP2). Convolutional layers C1 and C2 adopt kernels whose sizes are 1 × 1 and 3 × 3 respectively. By padding around the inputs on C1 and C2 layers, each layer maintained the same size as the input. C3, C4 and C5 incorporate 2 × 2 kernel sizes of and 2 × 2 strides without padding. With the same sizes, WP1 and WP2 layers are concatenated to C3 and C4 respectively to enhance the memory for low-frequency image features.

![Image text](https://github.com/arialibra/WCNN/blob/master/IMG-folder/wcnn.PNG)

By using wavelet decomposition, the image becomes scalable in the spatial direction, allowing accurate recognition of textures. The WCNN decomposes the image into a number of wavelet subbands, and reduces noisy data by filtering out high-frequency subbands. 

Test on Benmark Datasets and Human Thyroid OCT Image Datasets. From comparison between experimental results of WCNN and conventional CNNs, WCNN generates clear image edges, and improves the accuracy and consistency. The adoption of 2-level DTCWT shows significant effectiveness in eliminating noisy data and preserving the original 2D image texture.

( Article: Lu, Hongya, et al. "A dual-tree complex wavelet transform based convolutional neural network for human thyroid medical image segmentation." 2018 IEEE International Conference on Healthcare Informatics (ICHI). IEEE, 2018. )
