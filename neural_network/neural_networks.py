from utils import softmax_cross_entropy, add_momentum, data_loader_mnist, predict_label, DataSplit
import sys
import os
import argparse
import numpy as np
import json


# 1. One linear Neural Network layer with forward and backward steps
class linear_layer:

    """
        The linear (affine/fully-connected) module.

        It is built up with two arguments:
        - input_D: the dimensionality of the input example/instance of the forward pass
        - output_D: the dimensionality of the output example/instance of the forward pass

        It has two learnable parameters:
        - self.params['W']: the W matrix (numpy array) of shape input_D-by-output_D
        - self.params['b']: the b vector (numpy array) of shape 1-by-output_D

        It will record the partial derivatives of loss w.r.t. self.params['W'] and self.params['b'] in:
        - self.gradient['W']: input_D-by-output_D numpy array
        - self.gradient['b']: 1-by-output_D numpy array
    """

    def __init__(self, input_D, output_D):

        self.params = dict()
        self.gradient = dict()

        self.params['W'] = np.random.normal(loc=0.0, scale=0.1, size=(input_D, output_D))
        self.params['b'] = np.random.normal(loc=0.0, scale=0.1, size=(1, output_D))

        self.gradient['W'] = np.zeros((input_D, output_D))
        self.gradient['b'] = np.zeros((1, output_D))


    def forward(self, X):

        """
            The forward pass of the linear (affine/fully-connected) module.

            Input:
            - X: A N-by-input_D numpy array, where each 'row' is an input example/instance (N is the batch size)

            Return:
            - forward_output: A N-by-output_D numpy array, where each 'row' is an output example/instance.
        """
        '''
        1. forward_ouput is like a logits (pre-activation outputs). It represent the raw score that come out of a linear layer 
        '''

        forward_output = X @ self.params['W'] + self.params['b']

        return forward_output

    def backward(self, X, grad):

        """
            The backward pass of the linear (affine/fully-connected) module.

            Input:
            - X: A N-by-input_D numpy array, the input to the forward pass.
            - grad: A N-by-output_D numpy array, where each 'row' (say row i) is the partial derivative of the mini-batch loss
                 w.r.t. forward_output[i].

            Operation:
            - Compute the partial derivatives (gradients) of the mini-batch loss w.r.t. self.params['W'], self.params['b'].
            
            Return:
            - backward_output: A N-by-input_D numpy array, where each 'row' (say row i) is the partial derivatives of the mini-batch loss w.r.t. X[i].
        """
        '''
        grad -> It is a gradient of the loss w.r.t the forward_output.
            These are the sensitivities of the loss to your output - use them to update your weights during training 

        Loss w.r.t w = X transposed * @ grad
            W[i][j] -> input feature i and output neuron j 
            How much does changing W[i][j] affect the loss -> delta lost / delta w  -> self.gradient['W']
            We look at : 
                1. input feature X[:, i] (column i of X)
                2. Interacts with 
                3. loss gradient for output j (column j of grad)
            How much did feature i across all samples affect the loss flowing into output neuron j? 
        '''

        self.gradient['W'] = X.T @ grad
        self.gradient['b'] = np.sum(grad, axis=0, keepdims=True)

        backward_output = grad @ self.params['W'].T

        return backward_output



# 2. ReLU Activation
class relu:

    """
        The relu (rectified linear unit) module.

        It is built up with NO arguments.
        It has no parameters to learn.
        self.mask is an attribute of relu. You can use it to store things (computed in the forward pass) for the use in the backward pass.
    """

    def __init__(self):
        self.mask = None

    def forward(self, X):

        """
            The forward pass of the relu (rectified linear unit) module.

            Input:
            - X: A numpy array of arbitrary shape.
            
            Return:
            - forward_output: A numpy array of the same shape of X
        """

        self.mask = X > 0
        forward_output = X * self.mask

        return forward_output

    def backward(self, X, grad):

        """
            The backward pass of the relu (rectified linear unit) module.

            Input:
            - X: A numpy array of arbitrary shape, the input to the forward pass.
            - grad: A numpy array of the same shape of X, where each element is the partial derivative of the mini-batch loss
                 w.r.t. the corresponding element in forward_output.

            Return:
            - backward_output: A numpy array of the same shape as X, where each element is the partial derivative of the mini-batch loss w.r.t. the corresponding element in  X.
        """
        backward_output = grad * self.mask


        return backward_output


# 3. tanh Activation
class tanh:

    def forward(self, X):

        """
            Input:
            - X: A numpy array of arbitrary shape.

            Return:
            - forward_output: A numpy array of the same shape of X
        """

        forward_output = np.tanh(X)

        return forward_output

    def backward(self, X, grad):

        """
            Input:
            - X: A numpy array of arbitrary shape, the input to the forward pass.
            - grad: A numpy array of the same shape of X, where each element is the partial derivative of the mini-batch loss w.r.t. the corresponding element in forward_output.

            Return:
            - backward_output: A numpy array of the same shape as X, where each element is the partial derivative of the mini-batch loss w.r.t. the corresponding element in  X.
        """

        tanh_x = np.tanh(X)  # re-compute tanh(X) if not stored
        derivative = 1 - tanh_x**2
        backward_output = grad * derivative

        return backward_output


# 4. Dropout
class dropout:

    """
        It is built up with one argument:
        - r: the dropout rate

        It has no parameters to learn.
        self.mask is an attribute of dropout. You can use it to store things (computed in the forward pass) for the use in the backward pass.
    """

    def __init__(self, r):
        self.r = r
        self.mask = None

    def forward(self, X, is_train):

        """
            Input:
            - X: A numpy array of arbitrary shape.
            - is_train: A boolean value. If False, no dropout should be performed.

            Operation:
            - Suppose p is uniformly randomly generated from [0,1]. If p >= self.r, output that element multiplied by (1.0 / (1 - self.r)); otherwise, output 0 for that element
            
            Return:
            - forward_output: A numpy array of the same shape of X (the output of dropout)
        """

        if is_train:
            self.mask = (np.random.uniform(0.0, 1.0, X.shape) >= self.r).astype(float) * (1.0 / (1.0 - self.r))
        else:
            self.mask = np.ones(X.shape)
        forward_output = np.multiply(X, self.mask)
        return forward_output

    def backward(self, X, grad):

        """
            Input:
            - X: A numpy array of arbitrary shape, the input to the forward pass.
            - grad: A numpy array of the same shape of X, where each element is the partial derivative of the mini-batch loss w.r.t. the corresponding element in forward_output.


            Return:
            - backward_output: A numpy array of the same shape as X, where each element is the partial derivative of the mini-batch loss w.r.t. the corresponding element in X.
        """

        backward_output = grad * self.mask
        return backward_output



# 5. Mini-batch Gradient Descent Optimization
def miniBatchGradientDescent(model, momentum, _alpha, _learning_rate):

    for module_name, module in model.items():

        # check if a module has learnable parameters
        if hasattr(module, 'params'):
            for key, _ in module.params.items():
                # This is the gradient for the parameter named "key" in this module
                g = module.gradient[key]

                if _alpha <= 0.0:
                    module.params[key] -= _learning_rate * g


                else:
                    momentum_key = module_name + '_' + key

                    # Update momentum: v = alpha * v_prev + learning_rate * gradient
                    momentum[momentum_key] = _alpha * momentum[momentum_key] + _learning_rate * g

                    # Update parameter using momentum
                    module.params[key] -= momentum[momentum_key]


    return model



def main(main_params):

    ### set the random seed. DO NOT MODIFY. ###
    np.random.seed(int(main_params['random_seed']))

    ### data processing ###
    Xtrain, Ytrain, Xval, Yval , _, _ = data_loader_mnist(dataset = main_params['input_file'])
    N_train, d = Xtrain.shape
    N_val, _ = Xval.shape

    index = np.arange(10)
    unique, counts = np.unique(Ytrain, return_counts=True)
    counts = dict(zip(unique, counts)).values()

    trainSet = DataSplit(Xtrain, Ytrain)
    valSet = DataSplit(Xval, Yval)

    ### building/defining MLP ###
    """
    In this script, we are going to build a MLP for a 10-class classification problem on MNIST.
    The network structure is input --> linear --> relu --> dropout --> linear --> softmax_cross_entropy loss
    the hidden_layer size (num_L1) is 1000
    the output_layer size (num_L2) is 10
    """
    model = dict()
    num_L1 = 1000
    num_L2 = 10

    # experimental setup
    num_epoch = int(main_params['num_epoch'])
    minibatch_size = int(main_params['minibatch_size'])

    # optimization setting
    _learning_rate = float(main_params['learning_rate'])
    _step = 10
    _alpha = float(main_params['alpha'])
    _dropout_rate = float(main_params['dropout_rate'])
    _activation = main_params['activation']


    if _activation == 'relu':
        act = relu
    else:
        act = tanh

    # create objects (modules) from the module classes
    model['L1'] = linear_layer(input_D = d, output_D = num_L1)
    model['nonlinear1'] = act()
    model['drop1'] = dropout(r = _dropout_rate)
    model['L2'] = linear_layer(input_D = num_L1, output_D = num_L2)
    model['loss'] = softmax_cross_entropy()

    # Momentum
    if _alpha > 0.0:
        momentum = add_momentum(model)
    else:
        momentum = None

    train_acc_record = []
    val_acc_record = []

    train_loss_record = []
    val_loss_record = []

    ### run training and validation ###
    for t in range(num_epoch):
        print('At epoch ' + str(t + 1))
        if (t % _step == 0) and (t != 0):
            _learning_rate = _learning_rate * 0.1

        idx_order = np.random.permutation(N_train)

        train_acc = 0.0
        train_loss = 0.0
        train_count = 0

        val_acc = 0.0
        val_count = 0
        val_loss = 0.0

        for i in range(int(np.floor(N_train / minibatch_size))):

            # get a mini-batch of data
            x, y = trainSet.get_example(idx_order[i * minibatch_size : (i + 1) * minibatch_size])

            ### forward pass ###
            a1 = model['L1'].forward(x)
            h1 = model['nonlinear1'].forward(a1)
            d1 = model['drop1'].forward(h1, is_train = True)
            a2 = model['L2'].forward(d1)
            loss = model['loss'].forward(a2, y)

            ### backward pass ###
            grad_a2 = model['loss'].backward(a2, y)
            grad_d1 = model['L2'].backward(d1, grad_a2)
            grad_h1 = model['drop1'].backward(h1, grad_d1)
            grad_a1 = model['nonlinear1'].backward(a1, grad_h1)

            grad_x = model['L1'].backward(x, grad_a1)

            ### gradient_update ###
            model = miniBatchGradientDescent(model, momentum, _alpha, _learning_rate)

        ### Computing training accuracy and obj ###
        for i in range(int(np.floor(N_train / minibatch_size))):

            x, y = trainSet.get_example(np.arange(i * minibatch_size, (i + 1) * minibatch_size))

            ### forward pass ###
            a1 = model['L1'].forward(x)
            h1 = model['nonlinear1'].forward(a1)
            d1 = model['drop1'].forward(h1, is_train = False)
            a2 = model['L2'].forward(d1)
            loss = model['loss'].forward(a2, y)
            train_loss += loss
            train_acc += np.sum(predict_label(a2) == y)
            train_count += len(y)

        train_acc = train_acc / train_count
        train_acc_record.append(train_acc)
        train_loss_record.append(train_loss)

        print('Training loss at epoch ' + str(t + 1) + ' is ' + str(train_loss))
        print('Training accuracy at epoch ' + str(t + 1) + ' is ' + str(train_acc))

        ### Computing validation accuracy ###
        for i in range(int(np.floor(N_val / minibatch_size))):

            x, y = valSet.get_example(np.arange(i * minibatch_size, (i + 1) * minibatch_size))

            ### forward pass ###
            a1 = model['L1'].forward(x)
            h1 = model['nonlinear1'].forward(a1)
            d1 = model['drop1'].forward(h1, is_train = False)
            a2 = model['L2'].forward(d1)
            loss = model['loss'].forward(a2, y)
            val_loss += loss
            val_acc += np.sum(predict_label(a2) == y)
            val_count += len(y)

        val_loss_record.append(val_loss)
        val_acc = val_acc / val_count
        val_acc_record.append(val_acc)

        print('Validation accuracy at epoch ' + str(t + 1) + ' is ' + str(val_acc))

    # save file
    json.dump({'train': train_acc_record, 'val': val_acc_record},
              open('MLP_lr' + str(main_params['learning_rate']) +
                   '_m' + str(main_params['alpha']) +
                   '_d' + str(main_params['dropout_rate']) +
                   '_a' + str(main_params['activation']) +
                   '.json', 'w'))

    print('Finish running!')
    return train_loss_record, val_loss_record



if __name__ == "__main__":


    ###################################################################################### 
    # These are the default arguments used to run your code.
    # These parameters will be changed while grading.
    # You can modify them to test your code (this does not affect the grading as long as
    # you remember to run runme.py before submitting).
    ######################################################################################

    parser = argparse.ArgumentParser()
    parser.add_argument('--random_seed', default=42)
    parser.add_argument('--learning_rate', default=0.01)
    parser.add_argument('--alpha', default=0.0)
    parser.add_argument('--dropout_rate', default=0.5)
    parser.add_argument('--num_epoch', default=10)
    parser.add_argument('--minibatch_size', default=5)
    parser.add_argument('--activation', default='relu')
    parser.add_argument('--input_file', default='mnist_subset.json')
    args = parser.parse_args()
    main_params = vars(args)
    main(main_params)
