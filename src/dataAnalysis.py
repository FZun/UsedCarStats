# -*- coding: utf-8 -*-

## standard packages
import math
import numpy as np
import matplotlib.pyplot as plt

import os
import collections
import json

import scipy as sp
import json

def pcascoreplot(scores, ncomponents=5, alpha=1, labels=[0], labelmap={0: 'b'},
                 legend=None, markersize=None, explained_variance=None, figsize=[4, 3]):

    colors = [labelmap[label] for label in labels]
    nplots = (ncomponents-1)**2
    fig, ax = plt.subplots(nrows=ncomponents-1, ncols=ncomponents-1, figsize=figsize)

    if nplots == 1:
        ax.scatter(scores[:, 0], scores[:, 1], s=40, c=colors, alpha=alpha, edgecolor=colors)
        ax.axhline(c='k')
        ax.axvline(c='k')
        if explained_variance is not None:
            ax.set_xlabel("PC % i, " % 1 + str(round(explained_variance[0]*100, 2)) + "%")
            ax.set_ylabel("PC % i, " % 2 + str(round(explained_variance[1]*100, 2)) + "%")
        else:
            ax.set_xlabel("PC % i" % 1)
            ax.set_ylabel("PC % i" % 2)
        if legend:
            for i, l in enumerate(legend):
                ax.scatter(None, None, marker='o', c=labelmap[i], edgecolor = labelmap[i], label=l)
            ax.legend(frameon=False, numpoints=1, loc='lower left')

    else:
        for i in range(0, ncomponents-1):
            for j in range(1, ncomponents):
                if i < j:
                    ax[i, j-1].scatter(scores[:, i], scores[:, j],
                                       c=colors, alpha=alpha, edgecolor=colors)
                    ax[i, j-1].axhline(c='k')
                    ax[i, j-1].axvline(c='k')
                    if explained_variance is not None:
                        ax[i, j-1].set_xlabel("PC % i, " % (i+1) + str(round(explained_variance[i]*100, 2)) + "%")
                        ax[i, j-1].set_ylabel("PC % i, " % (j+1) + str(round(explained_variance[j]*100, 2)) + "%")
                    else:
                        ax[i, j-1].set_xlabel("PC % i" % (i+1))
                        ax[i, j-1].set_ylabel("PC % i" % (j+1))
                else:
                    ax[i, j-1].set_axis_off()
        if legend:
            for i, l in enumerate(legend):
                ax[ncomponents-2, 0].scatter(None, None, marker='o', c=labelmap[i], edgecolor = labelmap[i], label=l)
            ax[ncomponents-2, 0].legend(frameon=False, numpoints=1, loc='lower left')
    return fig, ax
