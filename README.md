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

and source it with `source ~/.bashrc`

Check if installation was successful by issuing

`docker-remote -V` or `docker-remote --version`

<br>

Usage
----------


##### Searching

`docker-remote search <namespace>/<repository>`


##### Managing repository information

`docker-remote repository --size <namespace>/<repository>`


##### Managing descriptions

`docker-remote description <namespace>/<repository>`

`docker-remote description --full <repository>`

##### Managing tags

`docker-remote tags <namespace>/<repository>`

By default the output is in plain format, to pretty the output, use
`--pretty` option

If you wish to manipulate your repository, login is necessary.
In that case provide `-u` (short for `--login`) argument

`docker-remote --login username:password tags --remove -t <tagname>`

You can also remove all the tags in your repository:\
**[WARNING]** These operations *can NOT* be undone<br>

`docker-remote --login username:password tags --pop-all`

`docker-remote --login username:password tags --pop-back -n 2 <namespace>/<repository>`

You can even select how many tags you want to keep and discard the rest

`docker-remote --login username:password tags --pop-back -keep 3 <namespace>/<repository>`

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

###### TODOs and Suggestions 

- add support for description modifications
- pass tags to operate on with `namespace/repo:tag`
- create interactive session so that user could login only once
- consider implementing parent parser
- think of another implementation instead of millions of ifs...
