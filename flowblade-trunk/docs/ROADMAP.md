# FLOWBLADE ROADMAP

Last updated April 4th 2023.

### Media cache and project data folder

* Make possible to select folder where project media data is saved. Keep current XDG Data Directory as the default place.
* Make projects save rendered clips, proxies and containe clips data individual in data folder to enable moving and destroying data per project.

### GTK 4 port

* We will start gradually working towards doing GTK 4 through multiple releases. Adwaita dark theme looks promising and we will drop custom theming if possible.

### Video display

- Moving video display away from SDL 1.2 is still a long term goal, but there hasn't been a viable technology path to do that yet. Unfortunately SDL 2 no longer looks promising as the needed API for creating video displays for Wayland will likely never be available there.
