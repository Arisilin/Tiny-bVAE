import os
from lightning.pytorch.utilities.types import TRAIN_DATALOADERS
from torch import nn,optim,utils,Tensor
import lightning as L
from lightning.pytorch.loggers.wandb import WandbLogger
from torch.utils.data import DataLoader
from typing import Optional
from einops import rearrange, repeat, pack, reduce
import importlib, inspect


class DataInterface(L.LightningDataModule):
    logger: Optional[WandbLogger]
    def __init__(self,
                 num_workers=8,
                 dataset='',
                 **kwargs):
        super().__init__() 
        self.num_workers=num_workers
        self.dataset=dataset
        self.kwargs = kwargs
        self.batch_size = kwargs['batch_size']
        self.load_data_module()
    def setup(self, stage=None):
        # Assign train/val datasets for use in dataloaders
        if stage == 'fit' or stage is None:
            # TODO: Current Implementation doesnt break the loading and split into two part, bring the loading part to load_data and just load once.
            self.trainset = self.instancialize(train=True)
            self.valset = self.instancialize(train=False)

        # Assign test dataset for use in dataloader(s)
        if stage == 'test' or stage is None:
            self.testset = self.instancialize(train=False)

    def load_data_module(self):
        name = self.dataset
        camel_name = ''.join([i.capitalize() for i in name.split('_')])
        # dataset name also need to be snake name 
        # Change the `snake_case.py` file name to `CamelCase` class name.
        # Please always name your model file name as `snake_case.py` and
        # class name corresponding `CamelCase`.
        try:
            self.data_module = getattr(importlib.import_module(
                '.'+name, package=__package__), camel_name)
        except:
            raise ValueError(
                f'Invalid Dataset File Name or Invalid Class Name data.{name}.{camel_name}')

    def instancialize(self, **other_args):
        """ Instancialize a model using the corresponding parameters
            from self.hparams dictionary. You can also input any args
            to overwrite the corresponding value in self.kwargs.
        """
        class_args = inspect.getargspec(self.data_module.__init__).args[1:]
        inkeys = self.kwargs.keys()
        args1 = {}
        for arg in class_args:
            if arg in inkeys:
                args1[arg] = self.kwargs[arg]
        args1.update(other_args)
        return self.data_module(**args1)
    
    def train_dataloader(self):
        # print('Data Module len:',len(self.data_module))
        return DataLoader(self.trainset, batch_size=self.batch_size, num_workers=self.num_workers,pin_memory=True,persistent_workers=True, shuffle=True
                          )
    
    def val_dataloader(self):
        return DataLoader(self.valset, batch_size=self.batch_size, num_workers=self.num_workers,pin_memory=True,persistent_workers=True)
    
    def test_dataloader(self):
        return DataLoader(self.testset, batch_size=self.batch_size, num_workers=self.num_workers,pin_memory=True,persistent_workers=True)