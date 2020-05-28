## COMPOSITING 2+

In this document we have a list of ideas on how improve Compositng in Flowblade during 2.x  series.

## Alpha filters

* All shape creating Alpha filters to support the standard alpha combining operations:
  
  * OVERWRITE
  * ADD
  * SUBTRACK
  * INTERSECT
  * EXCLUDE
  
  

* Add Filter: **Alpha Blur**

## Compositors

* Create new  **Affine Motion Blur** Compositor 
* Individual Alpha Combiners **Alpha XOR**, **Alpha Out**, **Alpha In** replaced with a single **Porter-Duff** Compositor with all appropriate ops supported
* **LumaToAlpha** Compositor extended with standard alpha combining operations ops, see above

## 


