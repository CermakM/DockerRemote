# docker-remote

### Docker Hub remote repository manager

<br>

#### Installation:

python3 setup.py install --user

This should install the docker-remote executable in `~/.local/bin`. <br>
Make sure that the path to the executable is in the `PATH`, to do this,
add the following line to your `~/.bashrc` file

`export PATH="~/.local/bin/:$PATH"`

<br>

#### Usage:


##### Searching

`docker-remote search <namespace>/<repository>`

For official repositories just like:

`docker-remote search <repository>`


##### Managing descriptions

`docker-remote description <namespace>/<repository>`

`docker-remote description --full <repository>`

##### Managing tags

`docker-remote tags <repository>`

`docker-remote tags <namespace>/<repository>`

If you wish to manipulate your repository, login is necessary.
In that case provide `-u` (short for `--login`) argument

`docker-remote --login username:password tags --remove -t <tagname>`

**[WARNING]** This step can not be undone \
You can also remove all the tags in your repository:

`docker-remote --login username:password tags --remove --all`


<br>

###### TODO: operate tags with `namespace/repo:tag`

