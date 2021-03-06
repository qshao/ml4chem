import sys

sys.path.append("../../")
from ase.io import Trajectory
from dask.distributed import Client, LocalCluster
from ml4chem.data.handler import Data
from ml4chem.atomistic.features import LatentFeatures
from ml4chem.data.serialization import load
from ml4chem.utils import logger
import numpy as np


def autoencode():
    # Load the images with ASE
    latent_space = load("cu_training.latent")

    latent_load = []
    for e in list(latent_space.values()):
        for symbol, features in e:
            latent_load.append(features)

    latent_load = np.array(latent_load).flatten()

    images = Trajectory("cu_training.traj")
    purpose = "training"

    # Arguments for fingerprinting the images
    normalized = True

    data_handler = Data(images, purpose=purpose)
    images, energies = data_handler.get_data(purpose=purpose)

    preprocessor = ("MinMaxScaler", {"feature_range": (-1, 1)})

    features = (
        "Gaussian",
        {
            "cutoff": 6.5,
            "normalized": normalized,
            "preprocessor": preprocessor,
            "save_preprocessor": "inference.scaler",
        },
    )
    encoder = {"model": "ml4chem.ml4c", "params": "ml4chem.params"}

    features = LatentFeatures(
        features=features,
        encoder=encoder,
        preprocessor=None,
        save_preprocessor="latent_space_min_max.scaler",
    )

    features = features.calculate(images, purpose=purpose, data=data_handler, svm=True)

    latent_svm = []
    for e in list(features.values()):
        for symbol, features in e:
            latent_svm.append(features)

    latent_svm = np.array(latent_svm).flatten()

    assert np.allclose(latent_load, latent_svm)


if __name__ == "__main__":
    logger("cu_inference.log")
    cluster = LocalCluster()
    client = Client(cluster)
    autoencode()
