"""UNESCO Institute of Statistics (UIS) data reader."""

import pandas as pd
from unesco_reader.config import PATHS
from unesco_reader import common
from zipfile import ZipFile


def available_datasets() -> pd.DataFrame:
    """Return a dataframe with available datasets, and relevant information"""

    return (pd.read_csv(PATHS.DATASETS / 'uis_datasets.csv')
            .assign(link=lambda df: df.dataset_code.apply(lambda x: f"{PATHS.BASE_URL}{x}.zip")))


DATASETS = available_datasets()


def format_metadata(metadata_df: pd.DataFrame) -> pd.DataFrame:
    """Format the metadata DataFrame

    Args:
        metadata_df: DataFrame containing metadata

    Returns:
        A metadata DataFrame pivoted so that metadata types are joined and stored in columns
    """

    return (metadata_df.groupby(by=['INDICATOR_ID', 'COUNTRY_ID', 'YEAR', 'TYPE'], as_index=False)
            ['METADATA']
            .apply(' / '.join)
            .pivot(index=['INDICATOR_ID', 'COUNTRY_ID', 'YEAR'], columns='TYPE', values='METADATA')
            .reset_index()
            .rename_axis(None, axis=1)
            )


def map_dataset_name(name: str) -> str:
    """Map a dataset to its code. Raise an error if the dataset is not found.
    """

    if name in DATASETS.dataset_name.values:
        return DATASETS.loc[DATASETS.dataset_name == name, 'dataset_code'].values[0]
    elif name in DATASETS.dataset_code.values:
        return name
    else:
        raise ValueError(f"Dataset not found: {name}")


def transform_data(folder: ZipFile, dataset_code: str) -> pd.DataFrame:
    """ """

    df = common.read_csv(folder, f"{dataset_code}_DATA_NATIONAL.csv")
    labels = common.read_csv(folder, f"{dataset_code}_LABEL.csv")
    countries = common.read_csv(folder, f"{dataset_code}_COUNTRY.csv")
    metadata = (common.read_csv(folder, f"{dataset_code}_METADATA.csv")
                .pipe(format_metadata)
                )

    return (df
            .assign(COUNTRY_NAME=lambda d: d.COUNTRY_ID.map(common.mapping_dict(countries)),
                  INDICATOR_NAME=lambda d: d.INDICATOR_ID.map(common.mapping_dict(labels)))
            .merge(metadata, on=['INDICATOR_ID', 'COUNTRY_ID', 'YEAR'], how='left')
          )


class UIS:
    """ """

    # available_datasets: ClassVar[list] = available_datasets()

    def __init__(self, dataset: str):
        self.__dataset_code = map_dataset_name(dataset)
        self.__dataset_name = DATASETS.loc[DATASETS.dataset_code == self.__dataset_code, 'dataset_name'].values[0]
        self.__url = DATASETS.loc[DATASETS.dataset_code == self.__dataset_code, 'link'].values[0]
        self.__dataset_category = DATASETS.loc[DATASETS.dataset_code == self.__dataset_code, 'dataset_category'].values[
            0]

        self.__folder = None
        self.__data = None

    @property
    def dataset_code(self):
        """Return dataset code"""
        return self.__dataset_code

    @property
    def dataset_name(self):
        """Return dataset name"""
        return self.__dataset_name

    @property
    def url(self):
        """Return dataset url"""
        return self.__url

    @property
    def dataset_category(self):
        """Return dataset category"""
        return self.__dataset_category

    def load_data(self):  # add path: str = None later
        """Load data to the object"""

        self.__folder = common.unzip_folder(self.__url)
        self.__data = transform_data(self.__folder, self.__dataset_code)

    def get_data(self):
        """Return data"""
        return self.__data

    def save_to_disk(self, path: str):
        """Save data to disk"""
        pass

    def dataset_info(self):
        """Return dataset information"""
        pass

    def describe(self, indicator: str = None):
        """Return dataset description"""
        pass
