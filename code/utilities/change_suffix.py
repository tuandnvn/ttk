import os
def change_suffix(self, directory, input_filter, input_replace, output_replace):
    for root, dirnames, filenames in os.walk(self.DIR_PARSED):
        for filename in fnmatch.filter(filenames, input_filter):
            old_file = os.path.join(root, filename)
            new_file = old_file[:-len(input_replace)] + output_replace
            os.rename(old_file, new_file)