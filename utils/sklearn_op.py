from sklearn.metrics import roc_curve
from sklearn.cluster import KMeans
from tqdm import tqdm

import tensorflow as tf
import numpy as np

def custom_roc_curve(labels, distances):
    '''
    custom roc curve, wrapper for roc_curve in sklearn.metrics
    Arg:
        laels : Numpy 1D array
            shoule be binary with 0 or 1
                0 - different images
                1 - same images
        distances : Numpy 1D array
            Closer two images, more likely them to be same image(positive)
                score should be minus
    Return:
         
    '''
    fpr, tpr, thr = roc_curve(labels, -distances, pos_label=1)
    return fpr, tpr, -thr

def k_mean_labeling(X_samples, n_clusters):
    '''KMeansClustering wrapper
    Args:
        X_samples - Numpy 2D array
            [n_sample, n_features]
        n_clusters - int
    '''
    kmc = KMeansClustering(X_samples=X_samples, n_clusters=n_clusters, print_option=False)
    return kmc.predict(predict_x=X_samples)

class KMeansClustering:
    def __init__(self, X_samples, n_clusters, print_option=True):
        '''
        Args:
            X_samples - Numpy 2D array
                [n_sample, n_features]
            n_clusters - int
            print_option - bool
                defaults to be True
         
        '''
        if print_option: print("Fitting X_samples starts")
        self.nfeatures = X_samples.shape[1]
        self.nclusters = n_clusters
        self.manager = KMeans(n_clusters=self.nclusters, random_state=0).fit(X_samples)
        if print_option: print("Fitting X_samples done")

    @property
    def centers(self):
        return self.manager.cluster_centers_

    def predict(self, predict_x):
        '''
        Args:
            predict_x - Numpy 2D array
                [n_predict, nfeatures]
        Return:
            label - Numpy 1D array
                [n_predict, ], whose values is [0, self.clusters)
        '''
        assert predict_x.shape[1] == self.nfeatures, "x should have the same features %d but %d"%(self.nfeatures, predict_x.shape[1])

        return self.manager.predict(predict_x)

    def k_hash(self, predict_x, session): 
        '''
        accerelated with tensorflow

        Bigger closer implemented with just simple negative

        Args:
            predict_x - Numpy 2D array [npredict, nfeatures]
        Return:
            k_hash - Numpy 2D array [npredict, n_clusters]
        '''
        assert predict_x.shape[1] == self.nfeatures, "x should have the same features %d but %d"%(self.nfeatures, predict_x.shape[1])
        npredict = predict_x.shape[0]
        batch_size = 2
        if npredict%batch_size!=0:
            predict_x = np.concatenate([predict_x, np.zeros([batch_size-npredict%batch_size, self.nfeatures])], axis=0) 
       
        inputs = tf.placeholder(tf.float32, [batch_size, self.nfeatures]) # [batch_size, nfeatures]
        centers = tf.convert_to_tensor(self.centers, dtype=tf.float32) # [n_clusters, nfeatures]
        
        negdist = tf.negative(
                    tf.reduce_sum(
                        tf.square( 
                            tf.subtract(
                                tf.expand_dims(inputs, axis=1),
                                tf.expand_dims(centers, axis=0))),
                        axis=-1)) # [batch_size, 1, nfeatures] [1, nclusters, nfeatures] => [bath_size, ncluster, nfeatures] => [batch_size, n_clusters]
        
        nbatch = len(predict_x)//batch_size
        k_hash = list()
        for b in tqdm(range(nbatch), ascii = True, desc="batch"):
            feed_dict = {inputs : predict_x[b*batch_size:(b+1)*batch_size]}
            k_hash.append(session.run(negdist, feed_dict=feed_dict))
        k_hash = np.concatenate(k_hash, axis=0)
        k_hash = k_hash[:npredict]

        return k_hash
