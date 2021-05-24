'''
name: pasteTransformation
version: 1.0

Vitaly Musatov 
emails:
latest.green(at)gmail(dot)com
vit.musatov(at)gmail(dot)com


########################## THANKS TO ###################################
Alexandr Antoshuk, Alexey Kuchinski, Ivan Busquets,
                Jed Smith, Nathan Rusch, Pete O'Connell, Sean Wallitsch
For ideas, materials and shared scripts.
########################################################################


The MIT License (MIT)

Copyright (c) 2017 Vitaly Musatov

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

'''

import nuke
import nukescripts 
import nuke.rotopaint as rp
import _curvelib as cl
import itertools

# MAIN FUNCTION

def pasteTransformation(link = False):

    TRANSFORM_TYPE_NODES =  ['Tracker4', 'Tracker3', 'Transform', 'Noise', 'Bezier', 'GridWarp2', "TransformMasked", 'Text2']
    ROTO_TYPE_NODES = ['Roto', 'RotoPaint' ,'SplineWarp3']
    GRIDWARP3_TYPE = ['GridWarp3']

    TRANSFORM_KNOBS_LIST = ['translate', 'rotate', 'scale', 'center']

    CORNER_PIN_KNOBS_LIST = ['to1', 'to2', 'to3', 'to4', 'from1', 'from2', 'from3', "from4"]

    selectedNode = nuke.selectedNode()
    selectedNodeClass = selectedNode.Class()

    # deselection
    selectedNode['selected'].setValue(False)

    #put a node into a group 
    tmpGroup = nuke.nodes.Group()
    with tmpGroup:
        clipboardNode = nuke.nodePaste(nukescripts.cut_paste_file())
        clipboardNodeClass = clipboardNode.Class()

    #############################-TRSC-COPYING-#############################

    #TRSC copying -> classic transformation
    if clipboardNodeClass in TRANSFORM_TYPE_NODES and selectedNodeClass in TRANSFORM_TYPE_NODES and link == False:

        copyKnobs(clipboardNode, selectedNode, TRANSFORM_KNOBS_LIST, '')
    
        labeler(clipboardNode, selectedNode, '', False)
    
    #TRSC copying -> GridWarp3
    if clipboardNodeClass in TRANSFORM_TYPE_NODES and selectedNodeClass in GRIDWARP3_TYPE and link == False:

        copyKnobs(clipboardNode, selectedNode, TRANSFORM_KNOBS_LIST, 'source_grid_transform_')

        labeler(clipboardNode, selectedNode, '', False)

    #TRSC copying -> Roto nodes
    if clipboardNodeClass in TRANSFORM_TYPE_NODES and selectedNodeClass in ROTO_TYPE_NODES and link == False:

        copyKnobsRoto(clipboardNode, selectedNode, TRANSFORM_KNOBS_LIST)

    #############################-TRSC-LINKING-#############################

    #TRSC linking -> classic transformation
    if clipboardNodeClass in TRANSFORM_TYPE_NODES and selectedNodeClass in TRANSFORM_TYPE_NODES and link == True:

        linkKnobs(clipboardNode, selectedNode, TRANSFORM_KNOBS_LIST, '')

        labeler(clipboardNode, selectedNode, '', True)

    #TRSC linking -> GridWarp3
    if clipboardNodeClass in TRANSFORM_TYPE_NODES and selectedNodeClass in GRIDWARP3_TYPE and link == True:

        linkKnobs(clipboardNode, selectedNode, TRANSFORM_KNOBS_LIST, 'source_grid_transform_')

        labeler(clipboardNode, selectedNode, '', True)
        
    #TRSC linking -> Roto nodes
    if clipboardNodeClass in TRANSFORM_TYPE_NODES and selectedNodeClass in ROTO_TYPE_NODES and link == True:

        linkKnobsRoto(clipboardNode, selectedNode, TRANSFORM_KNOBS_LIST)

    #############################-CORNERPIN-MARTIX-COPYING-#############################

    #CornerPin->Matrix->Roto
    if clipboardNodeClass == "CornerPin2D" and selectedNodeClass in ROTO_TYPE_NODES and (link == False):
        
        cornerPinToRoto(clipboardNode, selectedNode)

    #CornerPin->Matrix->GridWarp
    if clipboardNodeClass == "CornerPin2D" and selectedNodeClass in GRIDWARP3_TYPE and (link == False):
        
        cornerPinToGridWarp(clipboardNode, selectedNode)

    #CornerPin->Linking->CornerPin
    if (clipboardNodeClass == "CornerPin2D") and (selectedNodeClass == "CornerPin2D") and (link == True): 

        linkKnobs(clipboardNode, selectedNode, CORNER_PIN_KNOBS_LIST, '')

    #CornerPin->CornerPin_Matrix
    if (clipboardNodeClass == "CornerPin2D") and (selectedNodeClass == "CornerPin2D") and (link == False): 

        cornerPinToAnimatedMatrix(clipboardNode, selectedNode)        



    # delete group
    nuke.delete(tmpGroup)

    # return selection back
    selectedNode['selected'].setValue(True)
    selectedNode['hide_input'].setValue(True)
    selectedNode['hide_input'].setValue(False)

    return True





def copyKnobs(sourceNode, destNode, knobs_list, knobPrefix):
    for knob in knobs_list:
        destKnob = knobPrefix+knob
        destNode[destKnob].defaultValue()
        destNode[destKnob].fromScript(sourceNode[knob].toScript())

def copyKnobsRoto(sourceNode, destNode, knobs_list):
    # if layer is not selected select root 
    curvesKnob = destNode['curves']
    selectLayer = curvesKnob.getSelected() 
    
    if selectLayer == [] or selectLayer[0].name == "Root": # second condition used to solve a bug    
        
        #print "Root"

        rootLayerTransform = curvesKnob.rootLayer.getTransform()

        # Reset all transformation in layer
        rootLayerTransform.reset()

        # TRANSLATE
        translateKnob = sourceNode['translate']

        if translateKnob.isAnimated() == True and translateKnob.hasExpression() == False:
            # animation
            translateAnimationCurveX = translateKnob.animation(0)
            translateAnimationCurveY = translateKnob.animation(1)

            rootLayerTransform.setTranslationAnimCurve(0, convertAnimatiomCurveToAnimCurve(translateAnimationCurveX))
            rootLayerTransform.setTranslationAnimCurve(1, convertAnimatiomCurveToAnimCurve(translateAnimationCurveY))
       
        elif translateKnob.hasExpression() == True:
            # expression
            expressionX = translateKnob.animation(0).expression() 
            expressionY = translateKnob.animation(1).expression() 

            rootLayerTransform.getTranslationAnimCurve(0).expressionString = expressionX
            rootLayerTransform.getTranslationAnimCurve(0).useExpression = True

            rootLayerTransform.getTranslationAnimCurve(1).expressionString = expressionY
            rootLayerTransform.getTranslationAnimCurve(1).useExpression = True

        else:
            # static
            translateValueX = translateKnob.getValue()[0]
            translateValueY = translateKnob.getValue()[1]

            translateConstantCurveX = cl.AnimCurve()
            translateConstantCurveX.constantValue = translateValueX
            translateConstantCurveY = cl.AnimCurve()
            translateConstantCurveY.constantValue = translateValueY
            
            rootLayerTransform.setTranslationAnimCurve(0, translateConstantCurveX)
            rootLayerTransform.setTranslationAnimCurve(1, translateConstantCurveY)

        # ROTATE
        rotateKnob = sourceNode['rotate']

        if rotateKnob.isAnimated() == True and rotateKnob.hasExpression() == False:
            # animation
            rotateAnimationCurve = rotateKnob.animation(0)

            rootLayerTransform.setRotationAnimCurve(2, convertAnimatiomCurveToAnimCurve(rotateAnimationCurve))

        elif rotateKnob.hasExpression() == True:

            expression = rotateKnob.animation(0).expression() 

            rootLayerTransform.getRotationAnimCurve(2).expressionString = expression
            rootLayerTransform.getRotationAnimCurve(2).useExpression = True

        else:
            # constant
            rotateValue = rotateKnob.getValue()
            
            rotateConstantCurve = cl.AnimCurve()
            rotateConstantCurve.constantValue = rotateValue
            
            rootLayerTransform.setRotationAnimCurve(2, rotateConstantCurve)
 
        # SCALE
        scaleKnob = sourceNode['scale']

        if scaleKnob.isAnimated() == True and scaleKnob.hasExpression() == False:
            # animation
                
            scaleAnimationCurveX = scaleKnob.animation(0)
            scaleAnimationCurveY = scaleKnob.animation(1)
            if scaleAnimationCurveY == None:
                scaleAnimationCurveY = scaleAnimationCurveX

            rootLayerTransform.setScaleAnimCurve(0, convertAnimatiomCurveToAnimCurve(scaleAnimationCurveX))
            rootLayerTransform.setScaleAnimCurve(1, convertAnimatiomCurveToAnimCurve(scaleAnimationCurveY))

        elif scaleKnob.hasExpression() == True:
            # expression
            scaleAnimationCurveX = scaleKnob.animation(0)
            scaleAnimationCurveY = scaleKnob.animation(1)

            if scaleAnimationCurveY == None:
                scaleAnimationCurveY = scaleAnimationCurveX

            scaleExpressionX = scaleAnimationCurveX.expression()
            scaleExpressionY = scaleAnimationCurveY.expression()

            rootLayerTransform.getScaleAnimCurve(0).expressionString = scaleExpressionX
            rootLayerTransform.getScaleAnimCurve(0).useExpression = True

            rootLayerTransform.getScaleAnimCurve(1).expressionString = scaleExpressionX
            rootLayerTransform.getScaleAnimCurve(1).useExpression = True

        else:
            # constant
            if type(scaleKnob.getValue()) is  float:
                scaleValueX = scaleKnob.getValue()
                scaleValueY = scaleValueX
            elif type(scaleKnob.getValue()) is list:
                scaleValueX = scaleKnob.getValue()[0]
                scaleValueY = scaleKnob.getValue()[1]

            scaleConstantCurveX = cl.AnimCurve()
            scaleConstantCurveX.constantValue = scaleValueX
            scaleConstantCurveY = cl.AnimCurve()
            scaleConstantCurveY.constantValue = scaleValueY
            
            rootLayerTransform.setScaleAnimCurve(0, scaleConstantCurveX)
            rootLayerTransform.setScaleAnimCurve(1, scaleConstantCurveY)

        # CENTER

        centerKnob = sourceNode['center']
        
        if centerKnob.isAnimated() == True and centerKnob.hasExpression() == False:

            centerAnimationCurveX = centerKnob.animation(0)
            centerAnimationCurveY = centerKnob.animation(1)

            rootLayerTransform.setPivotPointAnimCurve(0, convertAnimatiomCurveToAnimCurve(centerAnimationCurveX))
            rootLayerTransform.setPivotPointAnimCurve(1, convertAnimatiomCurveToAnimCurve(centerAnimationCurveY))

        elif centerKnob.hasExpression() == True:
            # expression
            centerAnimationCurveX = centerKnob.animation(0)
            centerAnimationCurveY = centerKnob.animation(1)

            centerExpressionX = centerAnimationCurveX.expression()
            centerExpressionY = centerAnimationCurveY.expression()

            rootLayerTransform.getPivotPointAnimCurve(0).expressionString = centerExpressionX
            rootLayerTransform.getPivotPointAnimCurve(0).useExpression = True

            rootLayerTransform.getPivotPointAnimCurve(1).expressionString = centerExpressionY
            rootLayerTransform.getPivotPointAnimCurve(1).useExpression = True

        else:
            # constant

            centerValueX = centerKnob.getValue()[0]
            centerValueY = centerKnob.getValue()[1]

            centerConstantCurveX = cl.AnimCurve()
            centerConstantCurveX.constantValue = centerValueX
            centerConstantCurveY = cl.AnimCurve()
            centerConstantCurveY.constantValue = centerValueY
            
            rootLayerTransform.setPivotPointAnimCurve(0, centerConstantCurveX)
            rootLayerTransform.setPivotPointAnimCurve(1, centerConstantCurveY)
        
        labeler(sourceNode, destNode, "Root", False)
    
    else:
    # but if an element selected we use standart paste
        
        copyKnobs(sourceNode, destNode, knobs_list, '')
        
        labeler(sourceNode, destNode, selectLayer[0].name, False)

    curvesKnob.changed()


def linkKnobs(sourceNode, destNode, knobs_list, knobPrefix):
    for knob in knobs_list:
        destKnob = knobPrefix + knob
        destNode[destKnob].defaultValue() # reset knob
        destNode[destKnob].setExpression('parent.%s.%s' % (sourceNode.name(), knob))


def linkKnobsRoto(sourceNode, destNode, knobs_list):
    # if layer is not selected select root 
    curvesKnob = destNode['curves']
    selectLayer = curvesKnob.getSelected() 
    
    if selectLayer == [] or selectLayer[0].name == "Root": # second condition bug
        
        rootLayerTransform = curvesKnob.rootLayer.getTransform()

        # Reset all transformation in layer
        rootLayerTransform.reset()

        # TRANSLATE
        currentKnob = 'translate'
        
        rootLayerTransform.getTranslationAnimCurve(0).expressionString = 'parent.%s.translate.x' % sourceNode.name()
        rootLayerTransform.getTranslationAnimCurve(0).useExpression = True
        rootLayerTransform.getTranslationAnimCurve(1).expressionString = 'parent.%s.translate.y' % sourceNode.name()
        rootLayerTransform.getTranslationAnimCurve(1).useExpression = True
        
        # ROTATE
        currentKnob = 'rotate'
        
        rootLayerTransform.getRotationAnimCurve(2).expressionString = 'parent.%s.rotate' % sourceNode.name()
        rootLayerTransform.getRotationAnimCurve(2).useExpression = True

        # SCALE
        currentKnob = 'scale'
        
        rootLayerTransform.getScaleAnimCurve(0).expressionString = 'parent.%s.scale.w' % sourceNode.name()
        rootLayerTransform.getScaleAnimCurve(0).useExpression = True
        rootLayerTransform.getScaleAnimCurve(1).expressionString = 'parent.%s.scale.h' % sourceNode.name()
        rootLayerTransform.getScaleAnimCurve(1).useExpression = True

        # CENTER
        currentKnob = 'center'
        
        rootLayerTransform.getPivotPointAnimCurve(0).expressionString = 'parent.%s.center.x' % sourceNode.name()
        rootLayerTransform.getPivotPointAnimCurve(0).useExpression = True
        rootLayerTransform.getPivotPointAnimCurve(1).expressionString = 'parent.%s.center.y' % sourceNode.name()
        rootLayerTransform.getPivotPointAnimCurve(1).useExpression = True
        
        labeler(sourceNode, destNode, "Root", True)

    else: 
    # but if selected use standart paste

        linkKnobs(sourceNode, destNode, knobs_list, '')

        labeler(sourceNode, destNode, selectLayer[0].name, True)

    curvesKnob.changed()

    return True


def labeler(sourceNode, destNode, layerName, link = False):

    currentLabel = destNode['label'].getValue()
    splitedLabel = currentLabel.split('\n')

    if link == True:
        connection = "linked to"
    else:
        connection = "trans from"
    
    sourceNodeName = sourceNode['name'].value()

    label = "%s %s %s\n" % (layerName, connection, sourceNode['name'].value())

    filtredSplitedLabel = [elem for elem in splitedLabel if ((not layerName in elem) and (elem != ''))]

    filtredSplitedLabel.append(label)

    newLabel = '\n'.join(filtredSplitedLabel)

    destNode['label'].setValue(newLabel)  

    return True

def convertAnimatiomCurveToAnimCurve(sourceAnimatiomCurve):

    animCurve = cl.AnimCurve()

    for key in sourceAnimatiomCurve.keys():
        time = key.x
        value = key.y
        animCurve.addKey(time, value)

    return animCurve

def convertAnimCurveToAnimatiomCurve(sourceAnimCurve):

    knob = nuke.WH_Knob('fake_knob')
    AnimationCurve = nuke.AnimationCurve(knob, 0, "fake_animation")

    for i in xrange(sourceAnimCurve.getNumberOfKeys()):
        time = sourceAnimCurve.getKey(i).time
        value = sourceAnimCurve.getKey(i).value
        AnimationCurve.setKey(time, value)

    del knob

    return AnimationCurve

def getAnimatiomCurveFromTracker(trackerNode):
    # Tricky way to get keys for Tracker4 
    #
    knob = nuke.WH_Knob('fake_knob')
    AnimationCurve = nuke.AnimationCurve(knob, 0, "fake_animation")
    
    tracks = trackerNode['tracks'] 
    numColumns = 31 
    colTrackX = 2 
    colTrackY = 3 
    trackIdx = 0 # for the first track 
    
    for time in tracks.getKeyList():

        value = tracks.getValueAt(time,numColumns*trackIdx + colTrackY) 
        AnimationCurve.setKey(time, value)

    del knob

    return AnimationCurve

def convertCornerPinToMatrix(valuesTO, valuesFROM, invert = False ):

    valuesTO = list(itertools.chain(*valuesTO))
    valuesFROM = list(itertools.chain(*valuesFROM))
    #print (valuesTO, valuesFROM)

    matrixTo = nuke.math.Matrix4()
    matrixFrom = nuke.math.Matrix4()
    
    matrixTo.mapUnitSquareToQuad(*valuesTO)
    matrixFrom.mapUnitSquareToQuad(*valuesFROM)

    if invert == False:
        matrixFromCornerPin = matrixTo * matrixFrom.inverse()
    else:
        matrixFromCornerPin = matrixFrom * matrixTo.inverse()

    matrixFromCornerPin.transpose()

    return matrixFromCornerPin

def getCornerPinData(sourceNode):

    CORNER_PIN_TO = ['to1', 'to2', 'to3', 'to4']
    CORNER_PIN_FROM = ['from1', 'from2', 'from3', "from4"]
    
    ROTO_CLASS = ['Roto', 'RotoPaint']
    TRACKER = ['Tracker4']
    GRIDWARP3_TYPE = ['GridWarp3']

    isInverted = sourceNode['invert'].value()

    checkingKnob = sourceNode['to1']
    
    if checkingKnob.isAnimated() == True and checkingKnob.hasExpression() == False: 

        animationKeys = checkingKnob.animation(0)

    elif checkingKnob.hasExpression() == True:

        expression = checkingKnob.animation(0).expression()  #Roto1.curves.PlanarTrackLayer1.pt1
            
        splitedExpression = expression.split('.')
            
        #check for parent
        if splitedExpression[0] == "parent":
            del splitedExpression[0]
            
        nodeName = splitedExpression[0]
        nodeClass = nuke.toNode(nodeName).Class()

        if nodeClass in ROTO_CLASS:

            layer = splitedExpression[2]
            animCurve = nuke.toNode(nodeName)['curves'].toElement(layer).getTransform().getExtraMatrixAnimCurve(0, 1)

            animationKeys = convertAnimCurveToAnimatiomCurve(animCurve)

        elif nodeClass in TRACKER:

            tracker = nuke.toNode(nodeName)

            animationKeys = getAnimatiomCurveFromTracker(tracker)

        else:

            nuke.message("Unsupported linking in %s" % sourceNode.name())
            return False
    else:

        nuke.message("No animation in %s" % sourceNode.name())
        return False

    return animationKeys

def cornerPinToRoto(sourceNode, destNode):
    
    CORNER_PIN_TO = ['to1', 'to2', 'to3', 'to4']
    CORNER_PIN_FROM = ['from1', 'from2', 'from3', "from4"]

    isInverted = sourceNode['invert'].value()

    curvesKnob = destNode['curves']
    selectedLayer = curvesKnob.getSelected() 

    animationKeys = getCornerPinData(sourceNode)

    if animationKeys == False:

        return False

    for key in animationKeys.keys():
        
        time = key.x

        valuesTO = [sourceNode[knobTO].valueAt(time) for knobTO in CORNER_PIN_TO]
        valuesFROM = [sourceNode[knobFROM].valueAt(time) for knobFROM in CORNER_PIN_FROM]

        transformMatrix = convertCornerPinToMatrix(valuesTO, valuesFROM, isInverted)

        if selectedLayer == [] or selectedLayer[0].name == "Root":

            layerTransform = curvesKnob.rootLayer.getTransform()
            layerName = 'Root'
            
        else:
            
            layerTransform = selectedLayer[0].getTransform()
            layerName = selectedLayer[0].name


        for index in xrange(16):

            matrixAnimCurve = layerTransform.getExtraMatrixAnimCurve(0, index)
            matrixAnimCurve.addKey(time, transformMatrix[index])
    
    labeler(sourceNode, destNode, layerName, False)

    return True

def cornerPinToGridWarp(sourceNode, destNode):
    
    CORNER_PIN_TO = ['to1', 'to2', 'to3', 'to4']
    CORNER_PIN_FROM = ['from1', 'from2', 'from3', "from4"]

    isInverted = sourceNode['invert'].value()

    animationKeys = getCornerPinData(sourceNode)

    if animationKeys == False:

        return False

    matrixKnob = destNode['source_grid_transform_matrix']
    matrixKnob.setAnimated()

    for key in animationKeys.keys():
        
        time = key.x

        valuesTO = [sourceNode[knobTO].valueAt(time) for knobTO in CORNER_PIN_TO]
        valuesFROM = [sourceNode[knobFROM].valueAt(time) for knobFROM in CORNER_PIN_FROM]

        transformMatrix = convertCornerPinToMatrix(valuesTO, valuesFROM, isInverted)

        for index in xrange(16):

            matrixKnob.setValueAt(transformMatrix[index], time, index)

    labeler(sourceNode, destNode, "Source", False)

    return True

def cornerPinToAnimatedMatrix(sourceNode, destNode):

    CORNER_PIN_TO = ['to1', 'to2', 'to3', 'to4']
    CORNER_PIN_FROM = ['from1', 'from2', 'from3', "from4"]

    isInverted = sourceNode['invert'].value()

    animationKeys = getCornerPinData(sourceNode)

    if animationKeys == False:

        return False

    matrixKnob = destNode['transform_matrix']
    matrixKnob.setAnimated()

    for key in animationKeys.keys():
        
        time = key.x

        #print (time)
        
        valuesTO = [sourceNode[knobTO].valueAt(time) for knobTO in CORNER_PIN_TO]
        valuesFROM = [sourceNode[knobFROM].valueAt(time) for knobFROM in CORNER_PIN_FROM]

        transformMatrix = convertCornerPinToMatrix(valuesTO, valuesFROM, isInverted)

        for index in xrange(16):

            matrixKnob.setValueAt(transformMatrix[index], time, index)
    
    labeler(sourceNode, destNode, "", False)

    return True

def quickRefFrameCornerPin():

    selectedNode = nuke.selectedNode()    
    
    if selectedNode == []:

        False    

    CORNER_PIN_TO = ['to1', 'to2', 'to3', 'to4']
    CORNER_PIN_FROM = ['from1', 'from2', 'from3', "from4"]
    
    curFrame = nuke.frame()
    nodeName = selectedNode.name()

    if selectedNode.Class() == 'CornerPin2D':

        for index, knob in enumerate(CORNER_PIN_FROM):

            selectedNode[knob].setExpression('%s.%s(%d)' % (nodeName,CORNER_PIN_TO[index], curFrame))

    return True
    
