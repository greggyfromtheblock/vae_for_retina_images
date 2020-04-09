"""
Add plotting and introspection functions here
"""
from umap import UMAP
from sklearn.manifold import TSNE
import time
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
from torchvision import datasets, transforms
import numpy as np
import torch
import os
from tqdm import tqdm
import argparse
import sys
import skimage

from training import Encoder, VAEDataset
from utils import setup

import warnings
warnings.filterwarnings("ignore")


def normalize(image):
    return (image - image.min()) / (image.max() - image.min())


def add_slash(path):
    if path[-1] != '/':
        return path + "/"
    else:
        return(path)


if __name__ == '__main__':
#    parser = argparse.ArgumentParser(description="""Visualization of the Encoder""")
#    parser.add_argument("--no_aug",
#            action="store_true",
#            help="""in case there are no augmentations (flips, rotations...),
#            ignores the parts in the script that expect them""",
#            )

    FLAGS, logger = setup(running_script="./utils/introspection.py", config="config.json")
    print("FLAGS= ", FLAGS)

    imfolder = add_slash(os.path.abspath(FLAGS.input))
    csv_file = os.path.abspath(FLAGS.csv_input)
    latent_vector_size = FLAGS.zdim

    network_name = FLAGS.network_name
    path_prefix = FLAGS.path_prefix
    network_dir = f'{path_prefix}/{network_name}/'

    print("\nLoad Data as Tensors...")
    img_dataset = datasets.ImageFolder(
        imfolder,
        transform=transforms.Compose(
            [transforms.ToTensor(),]
            #                transforms.Normalize((0.5,), (0.5,))]
        ),
    )
    data = VAEDataset(img_dataset)
    print("\nSize of the dataset: {}\nShape of the single tensors: {}".format(len(data), data[0][0].shape))
    #print("\nSize of the dataset: {}\nShape of the single tensors: {}".format(len(data), data[0].shape))

#    args = parser.parse_args()
#    print("args =", args)
#    print("sys.argv = ", sys.argv)

    csv_df = pd.read_csv(csv_file, sep='\t')

    diagnoses = {
        "N": "normal fundus",
        "D": "proliferative retinopathy",
        "G": "glaucoma",
        "C": "cataract",
        "A": "age related macular degeneration",
        "H": "hypertensive retinopathy",
        "M": "myopia",
        # "ant": "anterior segment",
        # "no": "no fundus image",
    }
    number_of_diagnoses = len(diagnoses)
    data_size = len(data)
    print("data size = ", data_size, "len of the df = ", len(csv_df),
            "files in image folder: ", len(os.listdir(imfolder + '/images')))
    targets = np.zeros((data_size, number_of_diagnoses),  dtype=np.int8)

    angles = [x for x in range(-FLAGS.max_degree, -9)]
    angles.extend([x for x in range(10, FLAGS.max_degree+1)])
    angles.extend([x for x in range(-9, 10)])
    print("\nPossible Angles: {}\n".format(angles))
    print("\nBuild targets...")
    for i, jpg in tqdm(enumerate(os.listdir(imfolder + '/images'))):
        if "flipped" in jpg:
            jpg = jpg.replace("_flipped", "")
            if "angle" in jpg:
                for angle in angles:
                    jpg = jpg.replace("_rot_%i" % angle, "")
        test = csv_df.loc[csv_df['Fundus Image'] == jpg]
        if test.empty:
            continue
        row_number = csv_df.loc[csv_df['Fundus Image'] == jpg].index[0]
        for j, feature in enumerate(diagnoses.keys()):
            targets[i][j] = csv_df.iloc[row_number].at[feature]
#        if i % 100 == 0:
#            img = skimage.io.imread(imfolder + '/images/' + jpg)
#            print("image size: ", img.shape)

    print("Finished building targets...")

    # Load network
    trained_encoder = Encoder()
    trained_encoder.load_state_dict(torch.load(network_dir+f"{network_name}.pth"))

    print("Generate samples..")
    print('data shape: ', data[0][0].shape)
    #samples = torch.zeros((data_size, *data[0].shape))
    samples = torch.zeros((data_size, *data[0][0].shape))
    print('sample shape: ', samples[0][0].shape)
    encoded_samples = np.zeros((data_size, latent_vector_size))
    for i in tqdm(range(0, data_size, data_size)):
        samples[i] = data[i][0]

    print("\nStart encoding of each image...")
    features, _, _ = trained_encoder(samples)
    encoded_samples = features.detach().numpy()
    print("Finished encoding of each image...")

    os.makedirs(network_dir+"visualizations/", exist_ok=True)
    print('created dir: ',
            network_dir + '/' + 'visualizations/')
    print("Start Visualization...")
    # colormap = np.array(['darkorange', 'royalblue'])
    colormap = np.array(['g', 'r'])
    colormap_rev = np.array(['r', 'g'])

    for i, diagnosis in tqdm(enumerate(diagnoses.keys())):

        diagnosis_name = diagnoses[diagnosis]

        # tSNE Visualization of the encoded latent vector
        time_start = time.time()
        tsne = TSNE(random_state=123).fit_transform(encoded_samples)

        # U-Map Visualization
        clusterable_embedding = UMAP(
            n_neighbors=30,
            min_dist=0.0,
            n_components=2,
            random_state=42,
        ).fit_transform(encoded_samples)
        print("spawned diagnosis keys")
        quit()

        # orange_patch = mpatches.Patch(color=colormap[0], label=f'No {diagnoses[diagnosis]}')
        # blue_patch = mpatches.Patch(color=colormap[1], label=f'{diagnoses[diagnosis]}

        if diagnosis_name == "normal fundus":
            red_patch = mpatches.Patch(color=colormap_rev[0], label=f'no {diagnosis_name}')
            green_patch = mpatches.Patch(color=colormap_rev[1], label=f' {diagnosis_name}')

            plt.scatter(tsne[:, 0], tsne[:, 1], c=colormap_rev[targets[:, i]], s=100)
            # plt.legend(handles=[orange_patch, blue_patch])
            plt.legend(handles=[red_patch, green_patch])
            plt.title(f"tSNE-Visualization of diagnosis: {diagnosis_name}\n", fontsize=16, fontweight='bold')

            plt.savefig(
                f"{path_prefix}/{network_name}/visualizations/tsne_visualization_of_diagnosis_{diagnosis_name}.png")
            plt.show()
            plt.close()

            plt.scatter(clusterable_embedding[:, 0], clusterable_embedding[:, 1], c=colormap_rev[targets[:, i]], s=100,
                        label=colormap)

            # plt.legend(handles=[orange_patch, blue_patch])
            plt.legend(handles=[red_patch, green_patch])
            plt.title(f"UMAP-Visualization of diagnosis: {diagnosis_name}\n", fontsize=16, fontweight='bold')

            plt.savefig(
                f"{path_prefix}/{network_name}/visualizations/umap_visualization_of_diagnosis_{diagnosis_name}.png")
            plt.show()
            plt.close()

        else:
            green_patch = mpatches.Patch(color=colormap[0], label=f'no {diagnoses[diagnosis]}')
            red_patch = mpatches.Patch(color=colormap[1], label=f'{diagnoses[diagnosis]}')
            plt.scatter(tsne[:, 0], tsne[:, 1], c=colormap[targets[:, i]], s=100)

            plt.legend(handles=[green_patch, red_patch])
            plt.title(f"tSNE-Visualization of diagnosis: {diagnosis_name}\n", fontsize=16, fontweight='bold')

            plt.savefig(
                f"{path_prefix}/{network_name}/visualizations/tsne_visualization_of_diagnosis_{diagnosis_name}.png")
            plt.show()
            plt.close()

            plt.scatter(clusterable_embedding[:, 0], clusterable_embedding[:, 1], c=colormap[targets[:, i]], s=100,
                        label=colormap)

            # plt.legend(handles=[orange_patch, blue_patch])
            plt.legend(handles=[green_patch, red_patch])
            plt.title(f"UMAP-Visualization of diagnosis: {diagnosis_name}\n", fontsize=16, fontweight='bold')

            plt.savefig(f"{path_prefix}/{network_name}/visualizations/umap_visualization_of_diagnosis_{diagnosis_name}.png")
            plt.show()
            plt.close()

