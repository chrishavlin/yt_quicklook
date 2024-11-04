import numpy as np
import unyt
import yt
from yt.utilities.exceptions import YTUnidentifiedDataType
import numpy.typing as npt
import abc
from collections import defaultdict
from pathlib import Path
import json

class Sampler(abc.ABC):

    def __init__(self,
                 sample_name: str,
                 storage_dir: Path | str,
                 resolution: tuple[int, int, int] | None = None,
                 fields: list[tuple[str, str]] | None = None,
                 storage_dtype: str | None = None):

        if resolution is None:
            resolution = (128,) * 3

        if fields is None:
            fields = [('gas', 'density'), ('gas', 'temperature')]

        if storage_dtype is None:
            storage_dtype = 'float32'

        self.storage_dir = storage_dir
        self.storage_dtype = storage_dtype
        self.sample_name = sample_name
        self.resolution = resolution
        self.fields = fields
        self.values: dict[int, npt.ndarray] = {}
        self.field_extrema: dict[int, npt.ndarray] = {}
        self.field_units: dict[int, str] = {}
        self.field_key_map: dict[int, tuple[str, str]] = {}
        for ikey, field in enumerate(self.fields):
            self.field_key_map[ikey] = field

        self.field_key_map_r: dict[tuple[str, str], int] = {}
        for ikey, field in self.field_key_map.items():
            self.field_key_map_r[field] = ikey

    def _load_ds(self):
        try:
            ds = yt.load(self.sample_name)
        except (FileNotFoundError, YTUnidentifiedDataType):
            ds = yt.load_sample(self.sample_name)
        return ds

    @abc.abstractmethod
    def _create_frb(self, ds):
        pass

    def sample(self):
        """
        sample a dataset. Will populate .values, .field_extrema and .units
        """
        ds = self._load_ds()
        self._create_frb(ds)
        self._sample_all_data(ds)

        new_vals = {}
        for field, vals in self.values.items():
            new_vals[field] = vals.astype(self.storage_dtype)
        self.values = new_vals


    def _sample_all_data(self, ds):
        ad = ds.all_data()

        extrema = ad.quantities.extrema(self.fields)
        if isinstance(extrema, unyt.unyt_array):
            extrema = [extrema, ]
        for field, vals in zip(self.field_key_map.keys(), extrema):
            self.field_extrema[field] = vals.d.tolist()
            self.field_units[field] = str(vals.units)

    @property
    def metadata(self):
        attrs = ['field_extrema', 'field_units', 'sample_name',
                 'resolution', 'storage_dtype', 'fields',
                 'field_key_map',]
        mdict = {}
        for attr in attrs:
            mdict[attr] = getattr(self, attr)

        return mdict

    def write(self):

        output_dir = Path(self.storage_dir)
        if output_dir.is_dir() is False:
            output_dir.mkdir()

        output_dir = output_dir / self.sample_name
        if output_dir.is_dir() is False:
            output_dir.mkdir()

        mdict = self.metadata
        mdict_file = output_dir / 'metadata.json'
        with open(mdict_file, 'w') as fi:
            json.dump(mdict, fi, indent=4)

        for field, vals in self.values.items():
            ftype, fname = field
            field_file = output_dir / f"field_{ftype}_{fname}.npy"
            np.save(field_file, vals)


class GridSampler(Sampler):

    def _create_frb(self, ds):

        res = self.resolution
        fields = self.fields

        ag = ds.arbitrary_grid(ds.domain_left_edge, ds.domain_right_edge, res)
        for field in fields:
            self.values[field] = ag[field].d


samplers = defaultdict(lambda: GridSampler)


def sample_a_ds(sample: str, output_dir: str | Path):
    sampler = samplers[sample](sample, output_dir)
    sampler.sample()
    sampler.write()


