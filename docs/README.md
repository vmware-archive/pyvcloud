# Documentation Builds

## Overview

Pyvcloud uses [Sphinx](http://www.sphinx-doc.org/en/stable/index.html)
to build documentation and publish the output to [Github Pages]
(https://help.github.com/articles/configuring-a-publishing-source-for-github-pages/)
by committing it on the gh-pages branch. Sphinx generates documentation
by reading Python modules and extracting docstrings into HTML. Github
Pages serves up documentation online at https://vmware.github.io/pyvcloud.

Github Pages use Jekyll by default to serve up content. Pyvcloud doc
builds turn Jekyll off using a .nojekyll file, since Sphinx generates
everything we need.  This has a couple of advantages. First, it's
easier to build and test public documentation locally, which leads to
quick turnaround.  Second, it is difficult to publish docs formatted by
Sphinx using Jekyll.  We would rather spend the time adding more features
to pyvcloud.

Sphinx and Githb Pages setup is somewhat non-intuitive if you have not
done it before. See the last section for full details. You only need to
do that once whereas the steps in the next section need to happen for
every documentation change.

## Documentation Build Procedure

Documentation builds work by creating the HTML output in this directory,
then copying it to a second git clone where it can be checked in on
branch gh-pages.  We need two repos so that you can work in a normal branch
and still check in on gh-pages, which is only used for documentation. 

### Prepare a documentation clone repo ###

You must do this step the first time you do a documentation build.  Later
builds can use the same repo. 

Prepare the doc clone in another location. 
```shell
   git clone git@github.com:vmware/pyvcloud.git pyvcloud-docs
   export PYVCLOUD_DOCS=$PWD/pyvcloud-docs
```

### Build and copy docs to clone repo ###

Return to your regular repo and run the following commands from the 
docs directory to generate documentation.  
```shell
   pip3 install -r doc-requirements.txt  # Ensure Sphinx is installed
   sphinx-apidoc -f --separate -o source ../pyvcloud
   make html
   rsync -avr build/html/ $PYVCLOUD_DOCS
```

(-f option overwrites previous generated files; --separate generates 
separate pages.)

Test the build docs by bringing up $PYVCLOUD_DOCS/index.html in a browser
and ensuring everything looks OK.  If you see issues fix the docs and build
again. 

### Push to Github ###

Check in the generated documents from the doc clone. 
```shell
   cd $PYVCLOUD_DOCS
   git add .
   git commit -m "Documentation build"
   git push origin gh-pages
```   

That's it. Changes will be visible publicly in a few minutes.  Note that
this process will work whether you commit directly to pyvcloud.git or
use a pull request from a forked repo.  If you use a PR don't forget to
merge to pyvcloud.git or you won't see your changes.

## Documentation Project Setup

This section describes all the steps necessary to set up Sphinx
documentation on pyvcloud.git or any other project for that matter.
You don't need to do any of this for regular doc builds; these
instructions are here to help set up other projects or give hints when
there are problems.

### Enable Github Pages using content from gh-pages branch

In this step we'll set up pyvcloud.git to publish documentation from 
the gh-pages branch.  First make a clone of pyvcloud.git for doc builds. 

```shell
   git clone git@github.com:vmware/pyvcloud.git pyvcloud-docs
   export PYVCLOUD_DOCS=$PWD/pyvcloud-docs
```

Create the gh-pages branch and clear out all files.  **DO THIS VERY 
CAREFULLY AS IT WILL DESTROY UNCOMMITTED FILES AND CLEAR THE BRANCH. 
ENSURE YOU ARE IN THE RIGHT BRANCH/REPO!!**

```shell
   git branch gh-pages
   git symbolic-ref HEAD refs/heads/gh-pages
   rm .git/index
   git clean -fdx
```

Add index.html, commit, and push.  This is a placeholder so you can
switch Github to publish from the gh-pages branch.

```shell
   echo "Hello world!" > index.html
   git add .
   git commit -m "Added placeholder to commit gh-pages branch"
   git push origin gh-pages
```

Once this is done, navigate to https://github.com/pyvcloud.git, press
the Settings button, and enable Github Pages publication from "gh-pages
branch". Press Save. 

Confirm that the "Hello world!" page appears properly on 
https://vmware.github.io/pyvcloud.

### Set up Sphinx project

This step enables Sphinx documentation generation in the docs 
directory. Perform all steps in a branch in your usual repo for 
development.  First, set up Sphinx project files using sphinx-quickstart. 

```shell
   pip3 install Sphinx  # Ensure Sphinx is installed
   cd docs
   sphinx-quickstart
```

When running sphinx-quickstart the following options are preferred:

* Select y to split source and build directories in the root path.
* Select y to automatically insert Python module docstrings.
* Select y to create .nojekyll file on built HTML.

### Customize Sphinx configuration

Sphinx-quickstart generates a project structure in the source directory.  
Customize these starting with conf.py. 

* Set the path to find pyvcloud.vcd modules.
```python
   import os
   import sys
   sys.path.insert(0, os.path.abspath('../../pyvcloud/vcd'))
```

Next, ensure the html_theme is set to alabaster. Finally, configure the
html_sidebars to include about.html, navigation.html, and search.html:
```python
    html_sidebars = {
      '**': ['about.html', 'navigation.html', 'searchbox.html']
    }
```

### Edit files to generate desired HTML

Copy navigation.html from the alabaster Python installation to the \_templates
directory under source.  Edit it so that it generates static links to
project locations starting with the Github repo.

Edit source/index.rst to include an introduction and reference(s) to the 
pyvcloud.vcd file generated by sphinx-apidoc.  
