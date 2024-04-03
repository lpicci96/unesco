""" UIS User interface module


TODO: information function
TODO: UIS class for accessing data
TODO: set cache refresh schedule

"""

from unesco_reader.formatting import UISData
from unesco_reader.read import UISInfoScraper, get_zipfile
from tabulate import tabulate
import pandas as pd
from functools import lru_cache

CACHING: bool = True  # set to False to disable caching


@lru_cache
def fetch_info(refresh: bool = False) -> list[dict]:
    """Fetch information about the datasets available in the UIS database."""

    # Clear the cache if refresh is True or if caching is disabled
    if refresh or not CACHING:
        fetch_info.cache_clear()

    return UISInfoScraper.get_links()


def fetch_dataset_info(dataset_name: str, refresh: bool = False) -> dict:
    """Fetch information about a specific dataset."""

    # get dataset information
    datasets = fetch_info(refresh)
    for dataset in datasets:
        if dataset_name == dataset['name']:
            return dataset
    else:
        raise ValueError(f"Dataset not found: {dataset_name}. \nPlease select from the following datasets: "
                         f"{', '.join([name['name'] for name in datasets])}")


@lru_cache
def fetch_data(href, refresh: bool = False) -> UISData:
    """Fetch data from a url"""

    # Clear the cache if refresh is True or if caching is disabled
    if refresh or not CACHING:
        fetch_data.cache_clear()

    # get the data
    folder = get_zipfile(href)
    return UISData(folder)


def info(refresh: bool = False) -> None:
    """Display information about the data available in the UIS database.

    This function will print dataset names, themes, and date of the last update
    from the UIS website. NOTE: cache is used to store the data and prevent multiple
    requests to the UIS website. If you want to refresh the cache and get the latest data,
    set refresh=True.

    Args:
        refresh: if True, refresh the cache and fetch the links from the website

    """

    _info = fetch_info(refresh)
    headers = [key for key in _info[0].keys() if key != 'href']
    rows = [{k: v for k, v in item.items() if k != 'href'} for item in _info]
    rows_list = [list(row.values()) for row in rows]
    print(tabulate(rows_list, headers=headers, tablefmt="simple"))


class UIS:
    """Class for accessing data from the UIS database."""

    def __init__(self, dataset_name: str):
        self._dataset_info = fetch_dataset_info(dataset_name)  # get dataset information
        self._data = fetch_data(self._dataset_info['href'])  # get the data

    def refresh(self):
        """Refresh the data by fetching the latest data from the UIS website."""

        self._dataset_info = fetch_dataset_info(self._dataset_info['name'], refresh=True)
        self._data = fetch_data(self._dataset_info['href'], refresh=True)
        print("Data refreshed.")

    def info(self) -> None:
        """Display information about the dataset."""

        _info = [['latest update' if key == 'latest_update' else key, value]
                 for key, value in self._dataset_info.items() if key != 'href']

        # Use tabulate to format this list, specifying no headers and a plain format
        print(tabulate(_info, tablefmt="simple"))

    @property
    def name(self) -> str:
        """Return the name of the dataset."""
        return self._dataset_info['name']

    @property
    def theme(self) -> str:
        """Return the theme of the dataset."""
        return self._dataset_info['theme']

    @property
    def latest_update(self) -> str:
        """Return the date of the last update of the dataset."""
        return self._dataset_info['latest_update']

    def get_country_data(self, include_metadata: bool = False, region: str | None = None) -> pd.DataFrame:
        """Return the data as a pandas DataFrame.

            Args: include_metadata: if True, include metadata columns in the DataFrame region: the region id to
            filter the data by. This will keep only countries in the specified region.If None (default),
            all countries are returned. Run get_regions() to get information about available regions.

            Returns:
                country data as a pandas DataFrame
        """
        df = self._data.country_data

        # remove metadata columns if include_metadata is False
        if not include_metadata:
            df = df[['country_id', 'country_name', 'indicator_id', 'indicator_label', 'year', 'value']]

        if region is not None:  # if a region is specified, try filter the data
            if self._data.region_concordance is None:  # if regional data is not available, raise an error
                raise ValueError("Regional data is not available for this dataset.")

            if region not in self._data.region_concordance['region_id'].unique():  # if no region found, raise an error
                raise ValueError(f"Region ID not found: {region}")

            countries_in_region = self._data.region_concordance.loc[self._data.region_concordance['region_id'] == region, 'country_id']
            df = df[df['country_id'].isin(countries_in_region)]

        return df.reset_index(drop=True)

    def get_metadata(self) -> pd.DataFrame:
        """Return the metadata as a pandas DataFrame."""

        if self._data.metadata is None:
            raise ValueError("Metadata is not available for this dataset.")

        return self._data.metadata

    def get_region_data(self, include_metadata: bool = False) -> pd.DataFrame:
        """Return the regional data as a pandas DataFrame.

            Args:
                include_metadata: if True, include metadata columns in the DataFrame

            Returns:
                regional data as a pandas DataFrame

        """

        if self._data.region_data is None:
            raise ValueError("Regional data is not available for this dataset.")

        df = self._data.region_data

        if not include_metadata:
            df = df[['region_id','indicator_id', 'indicator_label', 'year', 'value']]

        return df

    def get_countries(self) -> pd.DataFrame:
        """Return the available countries and their information as a pandas DataFrame.

        The returned dataframe will containe county IDs as ISO3 codes and country names.

        """

        if self._data.country_concordance is None:
            raise ValueError("Information about countries is not available for this dataset.")

        return self._data.country_concordance

    def get_regions(self) -> pd.DataFrame:
        """Return the available regions and their information as a pandas DataFrame.

        The returned dataframe will contain region IDs, country id and name that belong to the region,
        the entity that groups countries (eg WB for World Bank regions), and the region name.
        """

        if self._data.region_concordance is None:
            raise ValueError("Information about regions is not available for this dataset.")

        return self._data.region_concordance

    def get_variables(self) -> pd.DataFrame:
        """Return the available variables and their information as a pandas DataFrame.

        The returned dataframe will contain variable IDs, variable names, and descriptions.
        """

        if self._data.variable_concordance is None:
            raise ValueError("Information about variables is not available for this dataset.")

        return self._data.variable_concordance

    @property
    def readme(self) -> str:
        """Return the readme file as a string."""
        if self._data.readme is None:
            raise ValueError("Readme file is not available for this dataset.")
        return self._data.readme

    def display_readme(self) -> None:
        """Display the readme file."""

        print(self.readme)
