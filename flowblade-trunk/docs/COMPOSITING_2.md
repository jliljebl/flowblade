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
  * **Transform** renamed **Affine** and GUI box Translate editor displayed on top
  * **Picture in Picture** dropped
  * **Region** renamed **Wipe Translate** with Wipe functionality displayed on top
  * **Add Fade** category renamed to **Add Fade/Wipe**
  * **Wipe Clip Length** renamed **Wipe In** and **Wipe Out** and moved to category **Add Fade/Wipe**
  * New **Wipe In** and **Wipe Out** Compositors gets same auto placement as **Fade In** and  **Fade Out** 
  *  **Wipe Out** get **Reverse** param set true
  * Individual Alpha Combiners **Alpha XOR**, **Alpha Out**, **Alpha In** replaced with a single **Porter-Duff** Compositor with all appropriate ops supported
  * **LumaToAlpha** Compositor extended with standard alpha combining operations ops, see above

## Tracks Compositing

  * **Auto  Compositing**  mode added, in  which compositing is done in more common the bottom-up order.  This kills all manual composite target track handling
  * Current way named **Top Down Compositing**
  * User can switch between these modes but we do not quarantee results staying the same




