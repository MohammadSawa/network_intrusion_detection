from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np
import pandas as pd


class DataCleaningPipeline(BaseEstimator, TransformerMixin):

    def __init__(self):
        
        self.final_features = ['Destination Port', 'Flow Duration', 'Total Fwd Packets',
                           'Total Length of Fwd Packets', 'Fwd Packet Length Max',
                           'Fwd Packet Length Min', 'Fwd Packet Length Mean',
                           'Bwd Packet Length Max', 'Bwd Packet Length Min', 'Flow Bytes/s',
                           'Flow Packets/s', 'Flow IAT Mean', 'Flow IAT Std', 'Flow IAT Max',
                           'Flow IAT Min', 'Fwd IAT Mean', 'Fwd IAT Std', 'Fwd IAT Min',
                           'Bwd IAT Total', 'Bwd IAT Mean', 'Bwd IAT Std', 'Bwd IAT Max',
                           'Bwd IAT Min', 'Fwd PSH Flags', 'Fwd URG Flags', 'Fwd Header Length',
                           'Bwd Header Length', 'Bwd Packets/s', 'Min Packet Length',
                           'Max Packet Length', 'Packet Length Mean', 'Packet Length Variance',
                           'FIN Flag Count', 'RST Flag Count', 'PSH Flag Count', 'ACK Flag Count',
                           'URG Flag Count', 'Down/Up Ratio', 'Init_Win_bytes_forward',
                           'Init_Win_bytes_backward', 'act_data_pkt_fwd', 'min_seg_size_forward',
                           'Active Mean', 'Active Std', 'Active Max', 'Active Min', 'Idle Std']
        pass

    def fit(self, X, y=None):
        
        return self

    def transform(self, X):
        
        X = X.reset_index(drop=True)
        
        
        X = self._fix_column_names(X)
        X = self._drop_duplicates(X)
        X = self._replace_infinite_with_null(X)
        X = self._drop_nulls(X)
        X = self._filter_features(X)
        
        
        X = X.reset_index(drop=True)
        
        print(f"data cleaned! Cleaned Data \n {X.head()}")
        print(f"feature names are: \n {X.columns}")
        return X

    def _fix_column_names(self, df):
        return df.rename(columns=lambda col: col.strip())

    def _drop_duplicates(self, df):
        return df.drop_duplicates()

    def _replace_infinite_with_null(self, df):
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        return df

    def _drop_nulls(self, df):
        df.dropna(inplace=True)
        return df

    def _filter_features(self, df):
        return df[self.final_features]