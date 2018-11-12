from abc import ABC
from abc import abstractmethod
import json
import os
from pathlib import Path
import queue
from shutil import copyfile
from shutil import rmtree


class Generator(ABC):
    @property
    def answers(self):
        """Getter for answers property.

        :return answers

        :rtype: dict
        """
        return self._answers

    @answers.setter
    def answers(self, answers):
        """Setter for answers property.

        :return answers

        :rtype: dict
        """
        self._answers = answers

    @property
    def template_name(self):
        """Getter for template_name property.

        :return template_name

        :rtype str
        """
        return self._template_name

    @template_name.setter
    def template_name(self, template_path):
        """Setter for template_name property.

        :return template_name

        :rtype str
        """
        # Split the absolute template path
        templates_path_parts = template_path.split("/ui/")
        # Assign template name
        self._template_name = templates_path_parts[
            len(templates_path_parts) - 1
        ]

    @property
    def new_project_dir(self):
        """Getter for new_project_dir property.

        :return new_project_dir

        :rtype str
        """
        return self._new_project_dir

    @new_project_dir.setter
    def new_project_dir(self, new_project_dir):
        """Setter for new_project_dir property.

        :return new_project_dir

        :rtype str
        """
        self._new_project_dir = new_project_dir

    @abstractmethod
    def generate(self):
        """Generate vCD UI Plugin from template."""
        pass

    def binary_search_file_by_name(self, alist, item):
        """Find file with given name in list of files.

        :return file

        :rtype Path
        """
        first = 0
        last = len(alist) - 1
        found = False

        while first <= last and not found:
            midpoint = int((first + last) / 2)

            if os.path.basename(os.path.abspath(alist[midpoint].absolute())) \
               == item:
                found = alist[midpoint]
            else:
                if item < alist[midpoint].name:
                    last = midpoint - 1
                else:
                    first = midpoint + 1

        return found

    def find_file(self, rootPath, fileName):
        """Find file with given name in given root directory.

        :return file

        :rtype Path
        """
        q = queue.Queue()
        q.put(Path(rootPath))

        while q.empty() is False:
            node = q.get()

            found = self.binary_search_file_by_name(list(node.iterdir()),
                                                    "manifest.json")

            if found is False:
                for entrie in node.iterdir():
                    if entrie.is_dir():
                        q.put(entrie)
            else:
                return found


class ExtGenerator(Generator):
    def __init__(self):
        """Constructs the ExtGenerator object."""

    def parse_manifest(self):
        """Find manifest.json in the template path.

        Read the file, parse it to dict and returns it,
        if no manifest file is found default dict will be
        returned.

        :return manifest

        :rtype dict
        """
        file = None

        try:
            file = Path(os.path.join(self.new_project_dir,
                                     'src/public/manifest.json'))
            raise Exception("manifest.json does not exist")
        except Exception:
            # Assign the file Path obj
            file = self.find_file(self.answers["template_path"],
                                  "manifest.json")

        # Check if file is found
        if file is not None:
            # Read the file
            with open(file, "r") as f:
                # Parse it to dict and returns it
                return json.loads(f.read())
        else:
            # Return default manifest values
            return {
                "urn": "vmware:vcloud:plugin:lifecycle",
                "name": "plugin-lifecycle",
                "containerVersion": "9.1.0",
                "version": "1.0.0",
                "scope": ["service-provider"],
                "permissions": [],
                "description": "",
                "vendor": "VMware",
                "license": "MIT",
                "link": "http://someurl.com",
                "module": "SubnavPluginModule",
                "route": "plugin-lifecycle"
            }

    def populate_manifest(self, basename, original_file_abs_path):
        """Open template file, read the file in-memory.

        Populate the data given from user, creates
        the manifest.json with the new data.
        """
        # Read the original file
        readFile = open(original_file_abs_path, "r")

        # Create the new file and write the content
        with open(basename, "w") as f:
            # Parse the json content of the file
            files_json = json.loads(readFile.read())
            # Close the readable stream
            readFile.close()

            # Loop through answers
            for key, value in self.answers.items():
                # If answer key exist in the json
                if key in files_json:
                    # And if it is scope or permissions
                    if key == 'scope' or key == 'permissions':
                        # And if there is no content
                        if len(self.answers[key]) < 1:
                            # Assign empty array
                            value = []
                        else:
                            # If it's list already
                            if isinstance(self.answers[key], list):
                                value = self.answers[key]
                            else:
                                # Create array of strings
                                value = self.answers[key].split(", ")

                    # Assign the value to origin json file
                    files_json[key] = value

            # Write the new json to the newly created file with sorted keys
            # and 4 spaces indentation
            f.write(json.dumps(files_json, sort_keys=True, indent=4))
            # Close the writable stream
            f.close()

    def generate_files(self, entrie_full_abs_path, new_entrie_path, entrie):
        """Generate vCD UI Plugin files.

        Manifest.json is populated with the
        data from the questions with
        which user has been promped.
        """
        # Base name of the file
        basename = os.path.basename(entrie_full_abs_path)

        # If the file is manifest.json
        if basename == 'manifest.json':
            # Generate new current working directory
            newCWD = os.path.join(self.new_project_dir,
                                  new_entrie_path.split(basename)[0][1:])
            oldCWD = os.getcwd()
            # Get in new current working directory
            os.chdir(newCWD)
            # Populate manifest.json file with the data from users answers
            self.populate_manifest(basename,
                                   os.path.abspath(entrie.absolute()))
            # Reset the current working directory
            os.chdir(oldCWD)
        else:
            # Copy the file from his original directory to his new one
            copyfile(os.path.abspath(entrie.absolute()),
                     os.path.join(self.new_project_dir, new_entrie_path[1:]))

    def copy_files(self, directory=None):
        """Generate vCD UI Plugin from template.

        :param Path directory
        """
        # Create queue for directories
        q = queue.Queue()
        # Put the start point directory
        q.put(directory)

        # Loop while q is not empty
        while q.empty() is not True:
            # Pop the first element from the queue
            node = q.get()

            # Loop through the node entries
            for entrie in node.iterdir():
                # Split the absolute path
                entrie_full_abs_path = os.path.abspath(entrie.absolute())
                entrie_parts = entrie_full_abs_path.split(self.template_name)
                # Get the relative path to the entrie
                new_entrie_path = entrie_parts[len(entrie_parts) - 1]

                # If entries is file
                if entrie.is_file():
                    self.generate_files(entrie_full_abs_path, new_entrie_path,
                                        entrie)
                # else if it is directory and it isn't node modules
                elif entrie.is_dir() and entrie.name != 'node_modules':
                    # Create the new directory
                    os.mkdir(os.path.join(self.new_project_dir,
                             new_entrie_path[1:]))

                    # Add the entrie to the queue to loop through his
                    # directories if any
                    q.put(entrie)

    def generate(self, projectPromptsFn, pluginPromptsFn):
        """Generate vCD UI Plugin from template."""
        # Assign answers
        self.answers = projectPromptsFn()
        # Assign template name
        self.template_name = self.answers["template_path"]
        # Construct the path of the new project
        self.new_project_dir = os.path.join(os.getcwd(),
                                            self.answers["projectName"])

        # Assign manifest.json
        self.manifest = self.parse_manifest()

        # Prompt user
        project_answers = pluginPromptsFn(self.manifest)

        # Collect answers
        self.answers = {**self.answers, **project_answers}

        # If this path exists remove it
        if os.path.exists(self.new_project_dir):
            rmtree(self.new_project_dir)

        # Create the directory to given path
        os.mkdir(self.new_project_dir)

        # Start copy files
        self.copy_files(Path(self.answers["template_path"]))
