from b26_toolkit.src.data_processing import correlation, shift_NVs
from b26_toolkit.src.plotting import plot_fluorescence_new, update_fluorescence
from src.core import Script, Parameter
from src.scripts import GalvoScanWithLightControl


# DEPRECIATED
# class Take_And_Correlate_Images(Script, QThread):
#     updateProgress = Signal(int)
#
#     _DEFAULT_SETTINGS = Parameter([
#         Parameter('baseline_image_path', '', str, 'path for data'),
#         Parameter('baseline_image_tag', '', str, 'some_name'),
#         Parameter('path', 'Z:/Lab/Cantilever/Measurements/__test_data_for_coding/', str, 'path for data'),
#         Parameter('tag', 'dummy_tag', str, 'tag for data'),
#         Parameter('save', True, bool, 'save data on/off'),
#         Parameter('new_image_center', [0,0], list, 'Center of new image to acquire for correlation'),
#         Parameter('new_image_width', 0.1, float, 'Height and Width in V of new image to take'),
#         Parameter('reset', False, bool, 'Reset Current Shift State')
#     ])
#
#     _INSTRUMENTS = {}
#     _SCRIPTS = {'GalvoScan': GalvoScanWithLightControl}
#
#     def __init__(self, instruments = None, name = None, settings = None, scripts = None, log_function = None, data_path = None):
#         """
#         Example of a script that emits a QT signal for the gui
#         Args:
#             name (optional): name of script, if empty same as class name
#             settings (optional): settings for this script, if empty same as default settings
#         """
#         Script.__init__(self, name, settings = settings, instruments = instruments, scripts = scripts, log_function= log_function, data_path = data_path)
#         QThread.__init__(self)
#
#         self.data = {'baseline_image': [], 'new_image': [], 'x_shift': 0, 'y_shift': 0}
#         #forward the galvo scan progress to the top layer
#         self.scripts['GalvoScan'].updateProgress.connect(lambda x: self.updateProgress.emit(x/2))
#
#         self._plot_type = 'two'
#
#     def _function(self):
#         """
#         # Tracks drift by correlating new and old images, and returns shift in pixels
#         """
#         # subtracts mean to sharpen each image and sharpen correlation
#         assert(self.settings['new_image_width'] < 1)
#
#         if self.settings['reset']:
#             self.data['x_shift'] = 0
#             self.data['y_shift'] = 0
#             self.settings['reset'] = False
#
#         self.baseline_image = Script.load_data(self.settings['baseline_image_path'], data_name_in='image_data')
#         self.bounds = Script.load_data(self.settings['baseline_image_path'], data_name_in='bounds')
#         baseline_image_sub = self.baseline_image - self.baseline_image.mean()
#
#         #compute new guess of where the POI should be based on last known shift
#         center_guess = ((self.settings['new_image_center'][0] + self.data['x_shift'],self.settings['new_image_center'][1] + self.data['x_shift']))
#
#         x_min = self.bounds[0][0]
#         x_max = self.bounds[1][0]
#         y_min = self.bounds[2][0]
#         y_max = self.bounds[3][0]
#         x_len = self.baseline_image.shape[1]
#         y_len = self.baseline_image.shape[0]
#         x_pixel_to_voltage= (x_max-x_min)/x_len
#         y_pixel_to_voltage= (y_max-y_min)/y_len
#
#         new_x_min = center_guess[0]-(self.settings['new_image_width']/2)
#         new_x_max = center_guess[0]+(self.settings['new_image_width']/2)
#         new_y_min = center_guess[1]-(self.settings['new_image_width']/2)
#         new_y_max = center_guess[1]+(self.settings['new_image_width']/2)
#
#         if new_x_min < -.5:
#             new_x_max += (-.5 - new_x_min)
#             new_x_min = -.5
#             self.log('Correlation: Left Boundary Reached')
#         elif new_x_max > .5:
#             new_x_min += (.5 - new_x_max)
#             new_x_min = .5
#             self.log('Correlation: Right Boundary Reached')
#         if new_y_min < -.5:
#             new_y_max += (-.5 - new_y_min)
#             new_y_min = -.5
#             self.log('Correlation: Lower Boundary Reached')
#         elif new_y_max > .5:
#             new_y_min += (.5 - new_y_max)
#             new_y_min = .5
#             self.log('Correlation: Upper Boundary Reached')
#
#         self.scripts['GalvoScan'].settings['point_a']['x'] = new_x_min
#         self.scripts['GalvoScan'].settings['point_b']['x'] = new_x_max
#         self.scripts['GalvoScan'].settings['point_a']['y'] = new_y_min
#         self.scripts['GalvoScan'].settings['point_b']['y'] = new_y_max
#
#         self.scripts['GalvoScan'].start()
#         self.scripts['GalvoScan'].wait()  #wait for scan to complete
#         self.new_image = self.scripts['GalvoScan'].data['image_data']
#
#         new_x_len = self.new_image.shape[1]
#         new_y_len = self.new_image.shape[0]
#         new_x_pixel_to_voltage = (new_x_max-new_x_min)/new_x_len
#         new_y_pixel_to_voltage = (new_y_max-new_y_min)/new_y_len
#
#         new_image_sub = self.new_image - self.new_image.mean()
#
#         if x_pixel_to_voltage < new_x_pixel_to_voltage:
#             size = int(round(baseline_image_sub.shape[0]/(new_x_pixel_to_voltage/x_pixel_to_voltage)))
#             size = (size,size)
#             baseline_image_sub_PIL = im.fromarray(baseline_image_sub)
#             baseline_image_sub_PIL = baseline_image_sub_PIL.resize(size)
#             new_side_len = (np.sqrt(np.array(list(baseline_image_sub_PIL.getdata())).shape[0]))
#             baseline_image_sub = np.reshape(np.array(list(baseline_image_sub_PIL.getdata())), (new_side_len, new_side_len))
#             x_pixel_to_voltage = (x_max-x_min)/baseline_image_sub.shape[1]
#             y_pixel_to_voltage = (y_max-y_min)/baseline_image_sub.shape[0]
#
#         elif x_pixel_to_voltage > new_x_pixel_to_voltage:
#             size = int(round(new_image_sub.shape[0]/(x_pixel_to_voltage/new_x_pixel_to_voltage)))
#             size = (size,size)
#             new_image_sub_PIL = im.fromarray(new_image_sub)
#             new_image_sub_PIL = new_image_sub_PIL.resize(size)
#             new_side_len = (np.sqrt(np.array(list(new_image_sub_PIL.getdata())).shape[0]))
#             new_image_sub = np.reshape(np.array(list(new_image_sub_PIL.getdata())), (new_side_len, new_side_len))
#             new_x_pixel_to_voltage = (new_x_max-new_x_min)/new_image_sub.shape[1]
#
#
#         #takes center part of baseline image
#         # x_len = len(baseline_image_sub[0])
#         # y_len = len(baseline_image_sub)
#         # old_image = baseline_image_sub[(x_len/4):(x_len*3/4),(y_len/4):(y_len*3/4)]
#
#         # correlate with new image. mode='valid' ignores all correlation points where an image is out of bounds. if baseline
#         # and new image are NxN, returns a (N/2)x(N/2) correlation
#         self.corr_image = signal.correlate2d(baseline_image_sub, new_image_sub)
#         y, x = np.unravel_index(np.argmax(self.corr_image), self.corr_image.shape)
#
#         x_expected_location = (self.settings['new_image_center'][0] - x_min)/x_pixel_to_voltage + new_image_sub.shape[1]/2
#         y_expected_location = (self.settings['new_image_center'][1] - y_min)/y_pixel_to_voltage + new_image_sub.shape[0]/2
#
#         #correct shift for change with respect to guess
#         self.data['x_shift'] = self.data['x_shift'] + ((x + 1)-x_expected_location)*x_pixel_to_voltage
#         self.data['y_shift'] = self.data['y_shift'] + ((y + 1)-y_expected_location)*y_pixel_to_voltage
#
#         self.data['baseline_image'] = baseline_image_sub
#         self.data['new_image'] = new_image_sub
#
#         self.updateProgress.emit(100)
#
#     def shift_coordinates(self, coordinates):
#         if isinstance(coordinates, list):
#             new_coordinates = list()
#             for coor in coordinates:
#                 new_x = coor[0] + self.data['x_shift']
#                 new_y = coor[1] + self.data['y_shift']
#                 new_coordinates.append((new_x,new_y))
#             return new_coordinates
#         elif isinstance(coordinates, tuple):
#             new_x = coordinates[0] + self.data['x_shift']
#             new_y = coordinates[1] + self.data['y_shift']
#             return ((new_x,new_y))
#         else:
#             raise ValueError
#
#     def plot(self, figure, figure2):
#         axes, axes_2 = self.get_axes(figure, figure2)
#         plot_fluorescence(self.data['baseline_image'], [self.bounds[0][0], self.bounds[1][0], self.bounds[3][0], self.bounds[2][0]], axes)
#         new_center = ((self.settings['new_image_center'][0] + self.data['x_shift'] - self.settings['new_image_width']/2, self.settings['new_image_center'][1] + self.data['y_shift'] - self.settings['new_image_width']/2))
#         patch = patches.Rectangle(new_center, self.settings['new_image_width'], self.settings['new_image_width'], fill = False)
#         axes.add_patch(patch)
#         self.scripts['GalvoScan'].plot(axes_2)


class Take_And_Correlate_Images_2(Script):
    '''
    Takes a galvo scan, compares it to a previous galvo scan to find the relative shift, and then updates a list of
    nvs based on this shift so that they will give the current coordinates of those nvs
    '''

    _DEFAULT_SETTINGS = [
        Parameter('use_trackpy', False, bool, 'Use trackpy to create artificial nv-only images to filter out background')
    ]

    _INSTRUMENTS = {}
    _SCRIPTS = {'GalvoScan': GalvoScanWithLightControl}

    def __init__(self, instruments = None, name = None, settings = None, scripts = None, log_function = None, data_path = None):
        """
        Example of a script that emits a QT signal for the gui
        Args:
            name (optional): name of script, if empty same as class name
            settings (optional): settings for this script, if empty same as default settings
        """
        Script.__init__(self, name, settings = settings, instruments = instruments, scripts = scripts, log_function= log_function, data_path = data_path)

        self.data = {'baseline_image': [], 'new_image': [], 'image_extent': [], 'old_nv_list':[], 'new_NV_list': [], 'correlation_image': []}

    def _function(self):
        """
        # Takes a new image, and correlates this with the image provided to baseline_image in self.data. It uses the
        determined pixel shift to calculate a shift for each of the nvs in the old_nv_list, which is given to it by
        a superscript, then store it as new_NV_list in data
        """

        if self.data['baseline_image'] == []:
            self.log('No baseline image avaliable. Taking baseline.')
        elif self.data['image_extent'] == []:
            self.log('No image extent avaliable. Script may have been run in error.')
        elif self.data['old_nv_list'] == []:
            self.log('No nv list avaliable. Scipt may have been run in error.')

        if not self.data['baseline_image'] == []:
            #use same settings as initial image
            scan = self.scripts['GalvoScan'].scripts['acquire_image']
            scan.settings['point_a']['x'] = self.data['image_extent'][0]
            scan.settings['point_b']['x'] = self.data['image_extent'][1]
            scan.settings['point_a']['y'] = self.data['image_extent'][3]
            scan.settings['point_b']['y'] = self.data['image_extent'][2]

            self.scripts['GalvoScan'].run()

            self.data['new_image'] = self.scripts['GalvoScan'].scripts['acquire_image'].data['image_data']

            dx_voltage, dy_voltage, self.data['correlation_image'] = correlation(self.data['baseline_image'],
                                                   self.data['image_extent'], self.data['new_image'],
                                                   self.data['image_extent'], use_trackpy=self.settings['use_trackpy'])

            self.data['new_NV_list'] = shift_NVs(dx_voltage, dy_voltage, self.data['old_nv_list'])

        else:
            self.scripts['GalvoScan'].run()
            self.data['baseline_image'] = self.scripts['GalvoScan'].data['image_data']

    def _plot(self, axes_list):
        '''
        Plots the newly taken galvo scan to axis 2, and the correlation image to axis 1
        Args:
            axes_list: list of axes to plot to. Uses two axes.

        '''
        data = self.scripts['GalvoScan'].data['image_data']
        extent = self.scripts['GalvoScan'].data['extent']
        plot_fluorescence_new(data, extent, axes_list[1])
        if not self.data['correlation_image'] == []:
            axes_list[0].imshow(self.data['correlation_image'])

    def _update_plot(self, axes_list):
        '''
        Plots the newly taken galvo scan to axis 2, and the correlation image to axis 1
        Args:
            axes_list: list of axes to plot to. Uses two axes.

        '''
        data = self.scripts['GalvoScan'].data['image_data']
        extent = self.scripts['GalvoScan'].data['extent']
        update_fluorescence(data, axes_list[1])
        if not self.data['correlation_image'] == []:
            axes_list[0].imshow(self.data['correlation_image'])


if __name__ == '__main__':
    script, failed, instr = Script.load_and_append({'Correlate_Images': 'Correlate_Images'})

    print(script)
    print(failed)
    print(instr)
