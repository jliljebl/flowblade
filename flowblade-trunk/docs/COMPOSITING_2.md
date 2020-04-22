## COMPOSITING 2+



## Alpha filters
  * All shape creating Alpha filters to support the standard alpha combining operations:

	* OVERWRITE
	* ADD
	* SUBTRACK
	* INTERSECT
	* EXCLUDE

	Ops called LIGHTEN, DARKEN (or min, max) are excluded, to be fully useful they would require every alpha filter to have opacity parameter.

  * Some new alpha filters added: **Alpha Blur**, **Alpha Levels**.


## Compositors
  * **Affine Motion Blur** Compositor created
  * Individual Alpha Combiners **Alpha XOR**, **Alpha Out**, **Alpha In** replaced with a single **Porter-Duff** Compositor with all appropriate ops supported
  * **LumaToAlpha** Compositor extended with standard alpha combining operations ops, see above

## Tracks Compositing
  * New Compositing mode **Standardt Auto** added with compositing bahaviour similar to most compositors.
  * Current way named **Top Down Compositing**
  * User can switch between these modes but we do not quarantee results staying the same




