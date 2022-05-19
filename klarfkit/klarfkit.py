#!/usr/bin/env python
# coding: utf-8

# In[112]:



import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import warnings


# In[149]:


class WaferMap:

    def __init__(self):
        self.sample_size = None
        self.die_pitch = None
        self.die_origin = None
        self.center_location = None
        self.defect_list = pd.DataFrame()

    def load_klarf(self, file, name=None):

        with open(file) as f:
            data = [i.strip() for i in f.readlines()]
        cols = []
        defects = []
        defect_collect = False
        for i in data:
            
            if "SampleSize" in i:
                if self.sample_size and self.sample_size != (float(i[:-1].split()[-1]) * 1000):
                    warnings.warn(f"Warning: Files contain inconsistant sample sizes! {self.sample_size/1000}mm vs {(float(i[:-1].split()[-1]))}mm!")
                self.sample_size = float(i[:-1].split()[-1]) * 1000
            
            elif "DiePitch" in i:
                if self.die_pitch and self.die_pitch != [float(j) for j in i[:-1].split(" ")[1:]]:
                    warnings.warn("Warning: Files contain inconsistent die sizes. Recommend setting die_line_alpha to 0 for plotting")
                self.die_pitch = [float(j) for j in i[:-1].split(" ")[1:]]
            
            elif "DieOrigin" in i:
                self.die_origin = [float(j) for j in i[:-1].split(" ")[1:]]
            
            elif "CenterLocation" in i:
                self.center_location = [float(j) for j in i[:-1].split(" ")[1:]]
            
            elif "DefectRecordSpec" in i:
                for j in i[:-1].split()[2::]:
                    cols.append(j)
            
            elif "DefectList" in i:
                defect_collect = True

            elif "SummarySpec" in i:
                defect_collect = False

            elif defect_collect:
                defects.append(i.replace(";", "").split())

        df = pd.DataFrame(defects, columns=cols).astype(float)
        df['_XACTUAL'] = (df['XINDEX'] * self.die_pitch[0]) + df['XREL'] - self.center_location[0]
        df['_YACTUAL'] = (df['YINDEX'] * self.die_pitch[1]) + df['YREL'] - self.center_location[1]

        if name:
            df['_KLARFNAME'] = name
        else:
            df['_KLARFNAME'] = file

        self.defect_list = pd.concat([self.defect_list, df]).reset_index(drop=True)

    def plot_wafer_map(self, color='_KLARFNAME', die_line_alpha=0.2, die_line_color='gray', *args, **kwargs):
        wafer_sin = (np.sin(np.arange(0, 2 * np.pi, 1 / 1000))) * self.sample_size / 2
        wafer_cos = (np.cos(np.arange(0, 2 * np.pi, 1 / 1000))) * self.sample_size / 2
        # Plot the wafer circle
        plt.plot(wafer_sin, wafer_cos, color='k', linewidth=0.3)

        for i in range(-int(self.sample_size // self.die_pitch[0]) - 10,
                       int(self.sample_size // self.die_pitch[0]) + 10):

            die_x_lines = self.center_location[0] + (i * self.die_pitch[0])
            height_squared = (self.sample_size / 2) ** 2 - die_x_lines ** 2
            if height_squared > 0:
                height = np.sqrt(height_squared)

                plt.vlines(die_x_lines,
                           -height,
                           height,
                           color=die_line_color,
                           alpha=die_line_alpha)

        for i in range(-int(self.sample_size // self.die_pitch[1]) - 10,
                       int(self.sample_size // self.die_pitch[1]) + 10):

            die_y_lines = self.center_location[1] + (i * self.die_pitch[1])
            width_squared = (self.sample_size / 2) ** 2 - die_y_lines ** 2
            if width_squared > 0:
                width = np.sqrt(width_squared)

                plt.hlines(die_y_lines,
                           -width,
                           width,
                           color=die_line_color,
                           alpha=die_line_alpha)

        if color in self.defect_list.columns:
            sns.scatterplot(x=self.defect_list['_XACTUAL'],
                            y=self.defect_list['_YACTUAL'],
                            hue=self.defect_list[color],
                            *args, **kwargs)

            plt.legend(loc='lower left')
        else:
            sns.scatterplot(x=self.defect_list['_XACTUAL'],
                            y=self.defect_list['_YACTUAL'],
                            color=color,
                            *args, **kwargs)

        plt.xlim(-self.sample_size / 2 - 2000, self.sample_size / 2 + 2000)
        plt.ylim(-self.sample_size / 2 - 2000, self.sample_size / 2 + 2000)
