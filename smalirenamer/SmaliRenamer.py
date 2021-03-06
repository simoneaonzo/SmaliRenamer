import fileinput
import os
import re


class SmaliRenamer(object):
    allowedClassName = re.compile("^[A-Za-z]([a-zA-Z0-9_]*\$?)*.smali$")
    allowedName = re.compile("^[a-zA-Z0-9_]*$")
    defaultClassPrefixName = "Class"
    compiledKeysRegex = ""  # re.compile
    smaliExt = ".smali"
    mapping = {}

    def __init__(self, decompiledApkFolder):
        self.check_if_is_folder_and_exist(decompiledApkFolder)
        self.smaliFolder = os.path.join(decompiledApkFolder, "smali/")
        self.check_if_is_folder_and_exist(self.smaliFolder)
        self.manifest = os.path.join(decompiledApkFolder, "AndroidManifest.xml")
        if not os.path.exists(self.manifest):
            raise Exception("The AndroidManifest.xml in path '" + self.manifest + "' doesn't exists")

    @staticmethod
    def check_if_is_folder_and_exist(folder):
        if not os.path.isdir(folder):
            raise Exception("The file '" + folder + "' isn't a folder")
        if not os.path.exists(folder):
            raise Exception("The folder '" + folder + "' doesn't exists")
        return

    def run(self):
        print("Generating mapping and renaming files in: " + self.smaliFolder)
        self.generate_mapping_and_rename_files()
        mappingSize = len(self.mapping)
        print("Mapping size: " + str(mappingSize))
        if mappingSize > 0:
            self.compiledKeysRegex = re.compile('|'.join(re.escape(s) for s in self.mapping))  # Compiled keys regex
            print("Replacing all occurrences in files...")
            self.replace_occurrences_in_files()
        else:
            print("No classes with bad name, skip replacing.")
        print("Job done!")

    def generate_mapping_and_rename_files(self):
        for root, dirs, files in os.walk(self.smaliFolder, topdown=False):
            for name in files:
                if name.endswith(self.smaliExt):
                    if not self.allowedClassName.match(name):  # Loop all smali files with non printable names
                        newName = self.sanitize(name)
                        if newName != name:
                            os.rename(os.path.join(root, name), os.path.join(root, newName))  # Rename the files
                else:
                    raise Exception("Only .smali file allowed: " + os.path.join(root, name))
            for name in dirs:
                if not self.allowedName.match(name):
                    raise Exception("Folder with invalid name: " + os.path.join(root, name))

    def replace_occurrences_in_files(self):
        for root, dirs, files in os.walk(self.smaliFolder, topdown=False):  # For all .smali files
            for file in files:
                self.edit_file_inplace(os.path.join(root, file))
        self.edit_file_inplace(self.manifest)  # For the AndroidManifest.xml

    def edit_file_inplace(self, filename):
        """" Search for every references to the old classes names and replace them with the new names """
        with fileinput.FileInput(filename, inplace=True) as openFile:
            for line in openFile:
                line = self.compiledKeysRegex.sub(lambda x: self.mapping[x.group()], line)  # GGWPBB
                print(line)  # Print the line into the file

    def check_and_add(self, name):
        """ If the name contains invalid characters generate a new name and add the new mapping """
        if not self.allowedName.match(name):
            if name not in self.mapping:
                tmpName = self.defaultClassPrefixName + str(len(self.mapping))
                self.mapping[name] = tmpName
                return tmpName
            else:
                return self.mapping[name]
        return name

    def sanitize(self, fileName):
        """ Replace the obfuscated class name with ClassX (X incremental integer) and return the new one """
        name = fileName[:-len(self.smaliExt)]
        newName = ""
        split = name.split("$")
        if len(split) > 1:
            for s in split:
                newName += self.check_and_add(s)  # Generate the mapping
                newName += "$"
            newName = newName[:-1]
        else:
            newName = self.check_and_add(name)
        return newName + self.smaliExt
