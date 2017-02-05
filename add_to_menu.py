import nuke
import pasteTransformation

#### ADD TO STANDART MENU
nuke.menu('Nuke').addCommand("Edit/Node/pasteTransformation(copy)", "pasteTransformation.pasteTransformation(link = False)", "alt+v")
nuke.menu('Nuke').addCommand("Edit/Node/pasteTransformation(link)", "pasteTransformation.pasteTransformation(link = True)", "shift+v")