# pasteTransformation for Nuke
###pasteTransformation is a tool for fast linking and copy transform values between nodes.
For linking is SHIFT+V. For copying is ALT+V.
Currently supported transfer: 
* Transforms/Trackers -> Tracker4, Tracker3, Transform, Noise, Bezier, GridWarp2, GridWarp3, TransformMasked, Text2  + Roto,  RotoPaint и SplineWarp3
(You can paste transformation into layers.)
* CornerPin2D -> Roto, RotoPaint, SplineWarp3, GridWarp3, CornerPin2D(transform_matrix ) (Supported only copying).

You can paste transformation into layers. If you don't select a particular layer then a transformation goes to a Root layer.
