# ROS Installs

This repository contains [wstool](https://github.com/vcstools/wstool) "rosinstall" files for the 
Personal Robotics Lab: related groups of packages installed from source control, usually used in
the context of a [catkin](http://wiki.ros.org/catkin) workspace.

## How-To

### Workspace Setup

`wstool` may be used for any kind of project, but is particularly relevant for catkin `src` folders.

We use ssh `git@github...` for repositories to take advantage of ssh keys. If you do not have
you keys setup please see [GitHub's how-to](https://help.github.com/articles/generating-ssh-keys)
or ask your system administrator.

1. Install wstools with `sudo apt-get update && sudo apt-get install python-wstool` or 
`pip install wstool` if you have not already
1. Create a workspace

        mkdir -p my_workspace/src
        cd my_workspace/src
        catkin_init_workspace # optionally init catkin workspace
        wstool init # init .rosinstall file

### Add External `*.rosinstall` Files to Your Project

To use the files in this repo, execute the following after running `wstool init` in your workspace src folder:
```
# add all herbpy repositories to your .rosinstall without duplicates
wstool merge ~/pr-rosinstalls/herbpy.rosinstall
wstool up # update/clone your .rosinstall repositories
```

### Add Additional Repositories to Your Project

To add an repository to your project's `.rosinstall` file, run the following after `wstool init`:
```
# add repository to .rosinstall
wstool set some_repo git@github.com:user/some_repo.git --git
wstool up # update/clone your .rosinstall repositories
```

### Add New PRL `*.rosinstall` File

Before committing a new file, make sure there is not already a rosinstall file that
covers your workspace but under a name you did not expect.

1. Prepare a new **clean** workspace

        mkdir -p new_workspace/src
        cd new_workspace/src
        wstool init
1. Install all repositories and verify it works as desired

        wstool set repo1 git@github.com:user/repo1.git --git 
        ... # repeat for all repos
        wstool up
    * Prefer `git@github...` to take advantage of ssh keys
1. Rename `.rosinstall` to something meaningful before committing

        cp .rosinstall ~/pr-rosinstall/skynet.rosinstall

