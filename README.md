# docker-remote

#### Docker Hub remote repository manager

<br>

Installation
------------

```
# If you don't have the project cloned yet
git clone https://github.com/CermakM/docker-remote

# cd into the project root folder
cd docker-remote

# Install along with dependencis
pip3 install --user .
```

This should install the docker-remote executable in `~/.local/bin/`. <br>
Make sure that the path to the executable is in the `PATH`, to do this,
add the following line to your `~/.bashrc` file.

`export PATH="~/.local/bin/:$PATH"`

<br>

Usage
----------


##### Searching

`docker-remote search <namespace>/<repository>`


##### Managing descriptions

`docker-remote description <namespace>/<repository>`

`docker-remote description --full <repository>`

##### Managing tags

`docker-remote tags <repository>`

`docker-remote tags <namespace>/<repository>`

If you wish to manipulate your repository, login is necessary.
In that case provide `-u` (short for `--login`) argument

`docker-remote --login username:password tags --remove -t <tagname>`

You can also remove all the tags in your repository:

`docker-remote --login username:password tags --remove --all`\
**[WARNING]** This operation *can NOT* be undone<br>

<br>

FAQ 
---
> How do I operate on official repositories (those without namespace)?

You can easily neglect the `<namespace>/`, just write f.e<br>

`docker-remote description fedora`

> Can I modify descriptions of my repository with docker-remote?

This is not possible at the moment, but will be in the bright future.

<br>

***

###### TODO 

- support for listing multiple pages (pager maybe)
- add support for description modifications
- pass tags to operate on with `namespace/repo:tag`
- create interactive session so that user could login only once
