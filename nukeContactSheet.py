#!/usr/bin/env python
# coding:utf-8
""":mod:`nukeContactSheetTmp` -- dummy module
===================================

.. module:: moduleName
   :platform: Unix
   :synopsis: module idea
"""
# Python built-in modules import

# Third-party modules import

# Mikros modules import

__author__ = "duda"
__copyright__ = "Copyright 2016, Mikros Image"


from sgtkLib import tkutil, tkm
import os, pprint, errno, argparse, sys, math

_USER_ = os.environ['USER']
_OUTPATH_ ="/s/prods/captain/_sandbox/" + _USER_ +"/ContactSheet"

tk, sgw, project = tkutil.getTk(fast=True, scriptName=_USER_)
sg = sgw._sg
# import nuke
#import nuke.rotopaint as rp


animFilter = {
        'filter_operator' : 'any',
        'filters':[
            ['published_file_type', 'name_is', 'PlayblastImageSequence'],
        ]
    }

exrFilter = {
        'filter_operator' : 'any',
        'filters':[
            ['published_file_type', 'name_is', 'CompoImageSequence'],
            ['published_file_type', 'name_is', 'GenericImageSequence'],
        ]
        }

#main call to SG api extract information from published files
def findShots(selecFilter={}, taskname='compo_precomp', seq='p00300', shotList=['Not']):
    if shotList[0] == 'Not':
        filterShotlist = ['entity', 'is_not', None]
    else:
        filterShotlist = ['entity.Shot.code', 'not_in',shotList]
    filters = [
        ['project', 'is', {'type':'Project', 'id':project.id}],
        ['task', 'name_is', taskname],
        ['entity', 'is_not', None],
        ['entity', 'type_is', 'Shot'],
        ['entity.Shot.sg_sequence','name_is', seq],
        selecFilter,
        filterShotlist
    ]

    res = {}
    for v in sg.find('PublishedFile', filters, ['code', 'entity', 'version_number', 'path', 'published_file_type', 'entity.Shot.sg_cut_in','entity.Shot.sg_cut_out','task','entity.Shot.sg_sequence'], order=[{'field_name':'created_at','direction':'desc'}]):

        entityName = v['entity']['name']
        if not entityName in res:
            res[entityName] = v
            res[entityName]['imgFormat'] = '.'+ v['path']['content_type'][v['path']['content_type'].find("/")+1:]

    return res

#find the masters shot for a sequence looking in SG
def findMasters(seq='s0300'):
    filters = [
        ['project', 'is', {'type':'Project', 'id':project.id}],
        ['sg_parent_sequence','name_is', seq]
    ]

    masters = {}
    for v in sg.find('CustomEntity02', filters, ['sg_shots_lighting','code'], order=[{'field_name':'version_number','direction':'desc'}]):
        masterName = v['code']
        if masterName.find('_m')>= 0:
            print masterName+ ': layout master will not be used'
        else:
            masters[masterName]={}
            masterShot = masterName.replace('_k','_p0')
            linkShots = []
            for i in range(len(v['sg_shots_lighting'])):
                if v['sg_shots_lighting'][i]['name'] != masterShot:
                    linkShots.append(v['sg_shots_lighting'][i]['name'])
            masters[masterName]['masterShot'] = masterShot
            masters[masterName]['subShots'] = linkShots
            linkShots.insert(0,masterShot)
            masters[masterName]['sortedShot'] = linkShots
    return masters

def findStatusTask(taskname = 'compo_precomp',shotList = ['s1300_p00220','s1300_p00200','s1300_p00880','s1300_p00340'],seq='s1300'):
    filters = [
        ['project', 'is', {'type':'Project', 'id':project.id}],
        ['content', 'is', taskname],
        ['entity', 'is_not', None],
        ['entity', 'type_is', 'Shot'],
        ['entity.Shot.sg_sequence','name_is', seq],
        ['entity.Shot.code', 'in',shotList]
    ]
    res={}
    for v in sg.find('Task', filters, ['code','entity','sg_status_artistique']):
        entityName = v['entity']['name']
        if not entityName in res:
            res[entityName]= v['sg_status_artistique']
    return res

def findMasterFromShot(seq='s0300',shotList = []):
    masters = findMasters(seq)
    for shot in shotList:
        hasMaster = False
        for key in masters:
            if shot in masters[key]['sortedShot'] and not hasMaster:
                hasMaster = True
                print shot + ' is in master: '+ key
        if not hasMaster:
            print shot + " don't have master!!!!!"



def getAvrageColor(frameNumber=[101,125,150], frame = '/s/prods/captain/sequences/s0300/s0300_p00480/compo/compo_precomp/publish/images/generic/v012/s0300_p00480-s0300_p00480-base-compo_precomp-v012.'):
    nodeList = []
    numberOfFrame = len(frameNumber)
    frameNumber = sorted(frameNumber)
    appendClipNode = nuke.nodes.AppendClip(firstFrame=frameNumber[0])
    nodeList.append(appendClipNode)
    for i in range(numberOfFrame):
        readFile = frame + str(frameNumber[i]).zfill(4)+'.exr'
        readNode = nuke.nodes.Read(file =readFile)
        appendClipNode.setInput(i,readNode)
        nodeList.append(readNode)
    curveToolNode = nuke.nodes.CurveTool(name = "CurveTool",avgframes=1)
    curveToolNode['ROI'].setValue([0,0,1968,1080])
    curveToolNode.setInput(0,appendClipNode)
    nuke.execute("CurveTool", frameNumber[0], (frameNumber[0]-1) + numberOfFrame)
    nodeList.append(curveToolNode)
    col = curveToolNode['intensitydata'].value()
    #clamp the color to a maximum 1
    for i in range(len(col)):
        if col[i] > 1:
            col[i] = 1
    for node in nodeList:
        nuke.delete(node)
    return col

def isFrameGood(fileIn = "/s/prods/captain/_sandbox/duda/images/sRGBtoSpi_ColorCheckerMikrosWrongColor.exr",dirIn = "/tmp"):
    fileOut = fileIn
    dirFiles = sorted(os.listdir(dirIn))
    incr = 0
    dirIn +="/"
    #check if the file exist
    if not os.path.isfile(fileOut):
        #check which frame is the closet from the file wanted
        while fileOut > (dirIn + dirFiles[incr]):
            incr += 1
            if incr > len(dirFiles)-1:
                incr -= 1
                if incr < 0:
                    incr = 0
                break
    #extract the number from the frame
        fileOut = dirIn + dirFiles[incr]
    numberOut = int(fileOut[fileOut.find('.')+1:fileOut.rfind('.')])
    return { 'filePath':fileOut, 'frameNumber': numberOut}


def checkDir(path = '/tmp'):
    if not os.path.exists(os.path.dirname(path)):
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

def getNewVersionNumber(path = '/tmp', type = 'jpg'):
    checkDir(path)
    listDir = os.listdir(path)
    movieFile = []
    #only keep file with pattern "type"
    for i in listDir:
        if i.rfind('_v') == 0 and os.path.isdir(path+i):
            movieFile.append(i)
    #if no file found return 0
    if len(movieFile) == 0:
        return '_v001'
    #else return the last movie created
    else:
        movieFile.sort(reverse = True)
        lastFile = movieFile[0]
        start = lastFile.find('_v')+2
        #end = lastFile.rfind('.')
        newNumber = int(lastFile[start:]) +1
        return "_v"+ str(newNumber).zfill(3)

#check if directory exist and return the proper path for the file in the writes nodes
def createFileOutput(path = "/tmp", seq = "s1300", masterName='',createMasterDir=False,createMasterGlobSeq=False):
    #createMasterDir and createMasterGlobSeq cannot be True at the same time
    if createMasterDir and createMasterGlobSeq:
        if masterName is not '':
            createMasterGlobSeq=False
        else:
            createMasterDir=False

    if createMasterDir:
        JPGpath = path+'/'+seq+"/Masters/"+masterName+"/JPG/"
        version = getNewVersionNumber(path=JPGpath,type = 'jpg')
        JPGpath = path+'/'+seq+"/Masters/"+masterName+"/JPG/"+version+"/"
        checkDir(JPGpath)
        JPG = JPGpath+masterName+version+".####.jpg"

        EXRpath = path+'/'+seq+"/Masters/"+masterName+"/EXR/"
        version = getNewVersionNumber(path=EXRpath,type = 'exr')
        EXRpath = path+'/'+seq+"/Masters/"+masterName+"/EXR/"+version+"/"
        checkDir(EXRpath)
        EXR = EXRpath+masterName+version+".####.exr"

        HDpath = path+'/'+seq+"/Masters/"+masterName+"/HD/"
        version = getNewVersionNumber(path=HDpath,type = 'jpg')
        HDpath = path+'/'+seq+"/Masters/"+masterName+"/HD/"+version+"/"
        checkDir(HDpath)
        HD = HDpath+masterName+version+".####.jpg"

        MoviePath = path+'/'+seq+"/Masters/"+masterName+"/Movie/"
        version = getNewVersionNumber(path=MoviePath,type = 'mov')
        MoviePath = path+'/'+seq+"/Masters/"+masterName+"/Movie/"+version+"/"
        checkDir(MoviePath)
        Movie = MoviePath+masterName+version+".mov"

    if createMasterGlobSeq:
        JPGpath = path+'/'+seq+"/Masters/Global/JPG/"
        version = getNewVersionNumber(path=JPGpath,type = 'jpg')
        JPGpath = path+'/'+seq+"/Masters/Global/JPG/"+version+"/"
        checkDir(JPGpath)
        JPG = JPGpath+seq+ version+".####.jpg"

        EXRpath = path+'/'+seq+"/Masters/Global/EXR/"
        version = getNewVersionNumber(path=EXRpath,type = 'exr')
        EXRpath = path+'/'+seq+"/Masters/Global/EXR/"+version+"/"
        checkDir(EXRpath)
        EXR = EXRpath+seq+version+".####.exr"

        HDpath = path+'/'+seq+"/Masters/Global/HD/"
        version = getNewVersionNumber(path=HDpath,type = 'jpg')
        HDpath = path+'/'+seq+"/Masters/Global/HD/"+version+"/"
        checkDir(HDpath)
        HD = HDpath+seq+ "HD" +version+".####.jpg"

        MoviePath = path+'/'+seq+"/Masters/Global/Movie/"
        version = getNewVersionNumber(path=MoviePath,type = 'mov')
        MoviePath = path+'/'+seq+"/Masters/Global/Movie/"+version+"/"
        checkDir(MoviePath)
        Movie = MoviePath+seq+ version+".mov"
    else:
        JPGpath = path+'/'+seq+"/FullContactSheet/JPG/"
        version = getNewVersionNumber(path=JPGpath,type = 'jpg')
        JPGpath = path+'/'+seq+"/FullContactSheet/JPG/"+version+"/"
        checkDir(JPGpath)
        JPG = JPGpath+seq+ version+".####.jpg"

        EXRpath = path+'/'+seq+"/FullContactSheet/EXR/"
        version = getNewVersionNumber(path=EXRpath,type = 'exr')
        EXRpath = path+'/'+seq+"/FullContactSheet/EXR/"+version+"/"
        checkDir(EXRpath)
        EXR = EXRpath+seq+version+".####.exr"

        HDpath = path+'/'+seq+"/FullContactSheet/HD/"
        version = getNewVersionNumber(path=HDpath,type = 'jpg')
        HDpath = path+'/'+seq+"/FullContactSheet/HD/"+version+"/"
        checkDir(HDpath)
        HD = HDpath+seq+ "HD" +version+".####.jpg"

        MoviePath = path+'/'+seq+"/FullContactSheet/Movie/"
        version = getNewVersionNumber(path=MoviePath,type = 'mov')
        MoviePath = path+'/'+seq+"/FullContactSheet/Movie/"+version+"/"
        checkDir(MoviePath)
        Movie = MoviePath+seq+ version+".mov"


    return {"JPG": JPG,"EXR": EXR,"HD": HD,"Movie": Movie}

def createShotPathDict(res = {},shotFrame = 'start'):
    shotPath = {}
    for entityName in res.keys():
        #add an entry with the shot number
        shotPath[entityName]={}
        print "\n" + entityName
        #store the name of the file without extension as well as the directory name
        rootFrame = res[entityName]['path']['local_path'][:res[entityName]['path']['local_path'].find('%04d')]
        rootDir = rootFrame[:rootFrame.rfind("/")]
        #store the image file format
        shotPath[entityName]['imageFormat'] = res[entityName]['imgFormat']
        #if the first frame is chosen for contactsheet
        if shotFrame == 'mid':
            #take the cut_in frame from shotgun data
            frame = str(int((res[entityName]['entity.Shot.sg_cut_in'] + res[entityName]['entity.Shot.sg_cut_out'])/2)).zfill(4)+shotPath[entityName]['imageFormat']
            tmpFullFile = rootFrame+frame
            #check if the frame exist if not go in the directory and chose the closest frame to the chosen frame in the directory
            fullFile = isFrameGood(fileIn = tmpFullFile,dirIn = rootDir)["filePath"]
            #put the chosen frame in the dictionary to be chosen as a contactsheet frame
            shotPath[entityName]['frame']=fullFile
        elif shotFrame == 'end':
            frame = str(res[entityName]['entity.Shot.sg_cut_out']).zfill(4)+shotPath[entityName]['imageFormat']
            tmpFullFile = rootFrame+frame
            #check if the frame exist if not go in the directory and chose the closest frame to the chosen frame in the directory
            fullFile = isFrameGood(fileIn = tmpFullFile,dirIn = rootDir)["filePath"]
            #put the chosen frame in the dictionary to be chosen as a contactsheet frame
            shotPath[entityName]['frame']=fullFile
        else:
            frame = str(res[entityName]['entity.Shot.sg_cut_in']).zfill(4)+shotPath[entityName]['imageFormat']
            tmpFullFile = rootFrame+frame
            #check if the frame exist if not go in the directory and chose the closest frame to the chosen frame in the directory
            fullFile = isFrameGood(fileIn = tmpFullFile,dirIn = rootDir)["filePath"]
            #put the chosen frame in the dictionary to be chosen as a contactsheet frame
            shotPath[entityName]['frame']=fullFile
            cutInMaster = res[entityName]['entity.Shot.sg_cut_in']
        shotPath[entityName]['allFrames']= res[entityName]['path']['local_path'][:res[entityName]['path']['local_path'].find('%04d')]+"""####"""+shotPath[entityName]['imageFormat']
        shotPath[entityName]['rootFrame']= rootFrame
        shotPath[entityName]['version'] = str(res[entityName]['version_number'])
        shotPath[entityName]['task'] = res[entityName]['task']['name']
        shotPath[entityName]['sequence']= res[entityName]['entity.Shot.sg_sequence']['name']
        if shotPath[entityName]['task'] != 'anim_main':
            status = findStatusTask(taskname = shotPath[entityName]['task'],shotList = [entityName],seq=shotPath[entityName]['sequence'])
            shotPath[entityName]['status']= status[entityName]
        else:
            shotPath[entityName]['status'] = 'wtg'

        #use the cut_in from shotgun or if the corresponding frame doesn't exist use the closest number
        cut_in = res[entityName]['entity.Shot.sg_cut_in']
        checkFrame = shotPath[entityName]['rootFrame']+str(cut_in).zfill(4)+shotPath[entityName]['imageFormat']
        NewcutIn = isFrameGood(fileIn = checkFrame,dirIn = rootDir)["frameNumber"]
        shotPath[entityName]['in']= NewcutIn

        #find the cut_out from shotgun or if the corresponding frame doesn't exist use the closest number
        cut_out = res[entityName]['entity.Shot.sg_cut_out']
        checkFrame = shotPath[entityName]['rootFrame']+str(cut_out).zfill(4)+shotPath[entityName]['imageFormat']
        NewcutOut = isFrameGood(fileIn = checkFrame,dirIn = rootDir)["frameNumber"]
        shotPath[entityName]['out']= NewcutOut

        #determine the mid point of the shot or if the corresponding frame doesn't exist use the closest number
        cut_mid = int((res[entityName]['entity.Shot.sg_cut_in'] + res[entityName]['entity.Shot.sg_cut_out'])/2)
        checkFrame = shotPath[entityName]['rootFrame']+str(cut_mid).zfill(4)+shotPath[entityName]['imageFormat']
        NewcutMid = isFrameGood(fileIn = checkFrame,dirIn = rootDir)["frameNumber"]
        shotPath[entityName]['mid']= NewcutMid

        shotPath[entityName]['averageFrame'] = [NewcutIn,NewcutMid,NewcutOut]
        print shotPath[entityName]['averageFrame']
    return shotPath



def createContactSheetMasters(shotFrame = 'start',nbColumns = 6,seq ="s0300",taskname='compo_precomp',lightOnly = False, master='All',render= True, display = False):
    import nuke
    import nuke.rotopaint as rp
    root = nuke.root()
    root['format'].setValue( 'HD_1080' )
    Xpos = 0
    Ypos =0
    commandline = "rv "
    #find the masters for the sequence
    mastersSeq = findMasters(seq=seq)
    #find the shot with exr file(part of lighting step)
    res = findShots(selecFilter=exrFilter,seq=seq,taskname=taskname)
    #if user want to see the anim in the contact sheet
    if not lightOnly:
        lightingShotFound = []
        for shot in res.keys():
            lightingShotFound.append(shot)
        resAnim = findShots(selecFilter=animFilter,seq=seq,taskname='anim_main',shotList=lightingShotFound)
        resAnim.update(res)
        res = resAnim

    #check that the masters correspond to shot ready to go
    for key in sorted(mastersSeq.keys()):
        try :
            res[mastersSeq[key]['masterShot']]
        except KeyError:
            print 'master: '+key + ' not ready'
            mastersSeq.pop(key,None)

    if master == 'All':
        for key in sorted(mastersSeq.keys()):
            masterSortedShot = mastersSeq[key]['sortedShot']
            masterName = key
            resMaster = res.copy()
            for keyShot in resMaster.keys():
                if keyShot not in masterSortedShot:
                    resMaster.pop(keyShot,None)
            shotPath = createShotPathDict(res=resMaster,shotFrame=shotFrame)
            fileOut = createMaster(Xpos = Xpos, Ypos = Ypos, shotPath=shotPath,masterShot= mastersSeq[key]['masterShot'],nbColumns = 6,seq = masterName,render=render, display= display)
            mult = len(masterSortedShot) +1
            Xpos += (250*mult)
            if display:
                commandline +=" "+ fileOut
        if display:
            os.system(commandline)
    else:
        try:
            mastersSeq[master]
        except KeyError:
            print "no master called: "+ master
        else:
            masterSortedShot = mastersSeq[master]['sortedShot']
            masterName = master
            masterShotName = mastersSeq[master]['masterShot']
            resMaster = res.copy()
            for keyShot in resMaster.keys():
                if keyShot not in masterSortedShot:
                    resMaster.pop(keyShot,None)
            shotPath = createShotPathDict(res=resMaster,shotFrame=shotFrame)
            fileOut = createMaster(Xpos = Xpos, Ypos = Ypos, shotPath=shotPath,masterShot= masterShotName,nbColumns = 6,seq = masterName,render=render, display = display)
            if display:
                commandline +=" "+ fileOut
                os.system(commandline)




def createMaster(Xpos = 0, Ypos = 0, shotPath={}, masterShot='',nbColumns = 6,seq = 's0300',render=True, display = False):
    import nuke
    import nuke.rotopaint as rp
    seqNumber =seq[:seq.find("_k")]
    fileOutPath = createFileOutput(path = _OUTPATH_, seq = seqNumber,masterName=seq,createMasterDir=True)
    previousXpos = Xpos
    masterTitleNode = None
    #number of shot in sequence
    nbShot = len(shotPath.keys())
    #height of contact sheet
    heightContactSheet = (int((nbShot)/nbColumns)+1)*1170
    if heightContactSheet == 0:
        heightContactSheet=1170
    #width of contactsheet
    widthContactSheet = 1920*nbColumns
    #average color for the shot
    averageColor=[]
    #average color for sequence
    totalAvColor=[0.0,0.0,0.0,1]
    # size of the color swath in the roto node
    sizeSquare = widthContactSheet/nbShot
    if sizeSquare > 500:
        sizeSquare = 500
    # shift for the color swatch
    shiftX = 0
    # input of the contactsheet
    input = 0
    #max and min cut for the sequence
    maxCutOut = 0
    minCutIn = 101

    #creation of the roto Node
    rotoNode = nuke.nodes.Roto(name = 'roto_'+seq,cliptype="no clip")
    rCurves = rotoNode['curves']
    root = rCurves.rootLayer

    #creation of the contactsheet node
    nbRows = int((nbShot-1)/nbColumns)+1 if int((nbShot-1)/nbColumns)> 0 else 1
    contactSheetNode = nuke.nodes.ContactSheet(name="contactSheet",rows=nbRows ,columns=nbColumns,roworder="TopBottom",width=widthContactSheet,height=heightContactSheet, center= True,gap = 50)
    transformContactSheet = nuke.nodes.Transform(name = "transformContactSheet"+seq)
    transformContactSheet['translate'].setValue([0,1080/2])
    transformContactSheet.setInput(0,contactSheetNode)
    #reformat node for the contact sheet
    #reformatGlobalNode = nuke.nodes.Reformat(type = "to box",box_fixed = True,resize = "none",box_width = widthContactSheet, box_height = heightContactSheet+(2160*2),black_outside = True,name = "reformatGlobal")
    #text node displaying the sequence number
    textSeqNode = nuke.nodes.Text2(message=seq,cliptype="no clip",global_font_scale=8.5,name="title"+seq)
    textSeqNode["box"].setValue([0,0,5000,1080])
    textSeqNode["font"].setValue('Captain Underpants', 'Regular')
    textSeqNodeTransform = nuke.nodes.Transform(name = "transformSeq_"+seq)
    textSeqNodeTransform['translate'].setValue([200,heightContactSheet+900+(2*1080)])
    textSeqNodeTransform.setInput(0,textSeqNode)
    #reformat for the roto node the height is the height of a swatch node
    reformatColAverage = nuke.nodes.Reformat(type="to box",box_fixed=True,resize="none",box_width=widthContactSheet,box_height=sizeSquare,center=False,pbb=True,name="reformatColAverage")
    #constant color for average sequence color
    constantNode = nuke.nodes.Constant(name="averageSeqColor")
    constantNodeTransform = nuke.nodes.Transform(name = "transformConst_"+seq,scale = 0.6)
    constantNodeTransform['translate'].setValue([widthContactSheet-(1920*2),heightContactSheet+1200+(2*1080)])
    constantNodeTransform.setInput(0,constantNode)
    #constant blackbg
    constantNodeBg = nuke.nodes.Constant(name="BG_"+seq)
    reformatNodeBg = nuke.nodes.Reformat(type = "to box",box_fixed = True,resize = "none",box_width = widthContactSheet, box_height = heightContactSheet+(2160*2),black_outside = True,name = "reformatBg_"+seq)
    reformatNodeBg.setInput(0,constantNodeBg)
    #import of the colorChart
    readColorChartNode = nuke.nodes.Read(file="/s/prods/captain/_sandbox/duda/images/sRGBtoSpi_ColorCheckerMikrosWrongColor.exr",name=seq+"_colorChart")
    readColorChartNodeTransform = nuke.nodes.Transform(name = "transformChart_"+seq,scale = 0.85)
    readColorChartNodeTransform['translate'].setValue([widthContactSheet-(1920),heightContactSheet+1080+(2*1080)])
    readColorChartNodeTransform.setInput(0,readColorChartNode)
    #create the reformatNode for the masterShot
    reformatMasterShot= nuke.nodes.Reformat(type="to box",box_fixed=True,resize="fit",box_width=1920*2,box_height=1170*2,center=True,pbb=True,name="reformatMasterShot_"+seq)
    transformMasterShot = nuke.nodes.Transform(name= "transformMasterShot_"+seq)
    transformMasterShot['center'].setValue([1920,1080])
    transformMasterShot['translate'].setValue([(widthContactSheet/2)-1920,heightContactSheet+800])
    transformMasterShot.setInput(0,reformatMasterShot)

    #merge of all the nodes
    mergeNode = nuke.nodes.Merge2(inputs=[reformatNodeBg,textSeqNodeTransform],name="merge_"+seq)
    mergeNode.setInput(3,readColorChartNodeTransform)
    mergeNode.setInput(4,reformatColAverage)
    mergeNode.setInput(5,constantNodeTransform)
    mergeNode.setInput(6,transformMasterShot)
    mergeNode.setInput(7,transformContactSheet)

    #write node
    writeFullNode = nuke.nodes.Write(name = seq + "Write", colorspace = "linear", file_type = "exr",file =fileOutPath["EXR"] )
    writeFullLutBurnNode = nuke.nodes.Write(name = seq + "WriteLutBurn", colorspace = "linear", file_type = "jpeg", _jpeg_sub_sampling = "4:2:2",file =fileOutPath["JPG"])
    writeFullLutBurnNode['_jpeg_quality'].setValue(0.75)
    writeHDNode = nuke.nodes.Write(name = seq + "WriteHD", colorspace = "linear", file_type = "jpeg", _jpeg_sub_sampling = "4:2:2",file =fileOutPath["HD"])
    writeHDNode['_jpeg_quality'].setValue(0.75)
    writeMovieNode = nuke.nodes.Write(name = seq + "WriteMovie", colorspace = "linear", file_type = "mov",file =fileOutPath["Movie"])
    colorConvertNode = nuke.nodes.OCIOColorSpace(in_colorspace="linear",out_colorspace="vd")
    reformatWriteHDNode = nuke.nodes.Reformat(type="to format",resize="fit",center=True,black_outside = True,name="reformatHD_"+seq)
    writeFullLutBurnNode.setInput(0,colorConvertNode)
    writeMovieNode.setInput(0,reformatWriteHDNode)
    colorConvertNode.setInput(0,mergeNode)
    writeFullNode.setInput(0,mergeNode)
    reformatWriteHDNode.setInput(0,colorConvertNode)
    writeHDNode.setInput(0,reformatWriteHDNode)

    for path in sorted(shotPath.keys()):
        cutIn, cutOut, cutMid = shotPath[path]['in'], shotPath[path]['out'],shotPath[path]['mid']
        frameNumber = shotPath[path]['averageFrame']
        textColor = [1,1,1,1]
        if cutOut > maxCutOut:
            maxCutOut = cutOut
        if cutIn < minCutIn:
            minCutIn = cutIn
        #get the average color for the shot for the exr image
        if shotPath[path]['imageFormat'] == '.exr':
            averageColor =getAvrageColor(frameNumber=frameNumber, frame=shotPath[path]['rootFrame'])
            totalAvColor[0]+=averageColor[0]
            totalAvColor[1]+=averageColor[1]
            totalAvColor[2]+=averageColor[2]
        #else if it's coming from anim_main just put black
        else:
            averageColor = [0,0,0]
        readNode = nuke.nodes.Read(file = shotPath[path]['frame'],first=cutIn,last=cutOut, name = "read_"+path,on_error ='nearestframe',after='loop')
        readNode.setXYpos(Xpos, Ypos)

        #add a shape to the rotoNode
        shape =rp.Shape(rCurves,type='bezier')
        shape.append([shiftX,sizeSquare])
        shape.append([shiftX + sizeSquare,sizeSquare])
        shape.append([shiftX + sizeSquare,0])
        shape.append([shiftX,0])
        shape.name = 'shape_'+path
        shapeAttr = shape.getAttributes()
        shapeAttr.set('r',averageColor[0])
        shapeAttr.set('g',averageColor[1])
        shapeAttr.set('b',averageColor[2])
        root.append(shape)

        reformatNode = nuke.nodes.Reformat(type = "to box",box_fixed = True,resize = "none",box_width = 1920, box_height = 1170,black_outside = True,name = "reformat_" + path)
        reformatNode.setInput(0,readNode)
        reformatNode.setXYpos(Xpos, Ypos +90)
        transformNode = nuke.nodes.Transform(name = "transform_"+path)
        transformNode['translate'].setValue([0,-45])
        transformNode.setXYpos(Xpos, Ypos +120)
        transformNode.setInput(0,reformatNode)
        if shotPath[path]['imageFormat'] == '.exr':
            if shotPath[path]['status'] == 'cmpt':
                textColor = [0,1,0,1]
        textNode = nuke.nodes.Text2(message=path + "    Task: " + shotPath[path]['task'] + "    Version: " + shotPath[path]['version'],cliptype="no clip",global_font_scale=.8,name="title"+path)
        textNode["box"].setValue([25,1050,1920,1160])
        textNode['color'].setValue(textColor)
        textNode["font"].setValue('Captain Underpants', 'Regular')
        textNode.setInput(0,transformNode)
        textNode.setXYpos(Xpos, Ypos +150)
        Xpos += 125
        if path == masterShot:
            masterTitleNode = nuke.toNode("title"+path)
        else:
            contactSheetNode.setInput(input,textNode)
            input+=1

        shiftX += sizeSquare

    #connect the masterShot to it's reformatNode
    reformatMasterShot.setInput(0,masterTitleNode)

    #set the average color for the sequence in the constant node
    if exrShot is not 0:
        avCol = [totalAvColor[0]/nbShot,totalAvColor[1]/nbShot,totalAvColor[2]/nbShot,1]
        constantNode['color'].setValue(avCol)

    #connection and position of the nodes for the comp
    centerX = (Xpos+previousXpos)/2
    reformatMasterShot.setXYpos(previousXpos, 350)
    transformMasterShot.setXYpos(previousXpos, 400)
    #reformatGlobalNode.setInput(0,contactSheetNode)
    contactSheetNode.setXYpos(centerX, 700)
    reformatColAverage.setInput(0,rotoNode)
    reformatColAverage.setXYpos((centerX)-200, 800)
    rotoNode.setXYpos((centerX)-200, 750)
    constantNodeBg.setXYpos((centerX)-400, 700)
    reformatNodeBg.setXYpos((centerX)-400, 800)
    transformContactSheet.setXYpos(centerX, 750)
    textSeqNode.setXYpos((centerX)+200, 750)
    textSeqNodeTransform.setXYpos((centerX)+200, 800)
    readColorChartNode.setXYpos((centerX)+400, 700)
    readColorChartNodeTransform.setXYpos((centerX)+400, 800)
    constantNode.setXYpos(centerX+600, 700)
    constantNodeTransform.setXYpos((centerX)+600, 800)
    mergeNode.setXYpos(centerX, 850)
    colorConvertNode.setXYpos(centerX + 200, 950)
    writeFullNode.setXYpos(centerX, 1050)
    writeFullLutBurnNode.setXYpos(centerX + 200, 1050)
    reformatWriteHDNode.setXYpos(centerX + 400, 1000)
    writeHDNode.setXYpos(centerX + 400, 1050)
    writeMovieNode.setXYpos(centerX + 600, 1050)

    #render the frame
    if render:
        nuke.execute(writeFullNode,1,1)
        nuke.execute(writeFullLutBurnNode,1,1)
        nuke.execute(writeHDNode,1,1)

    if display:
        return fileOutPath["JPG"]




def createContactSheetAllSequence(shotFrame = 'start',nbColumns = 6,seq ="s0300",taskname='compo_precomp',lightOnly = False, render=True,display = False, HDsplit=False):
    import nuke
    import nuke.rotopaint as rp
    root = nuke.root()
    root['format'].setValue( 'HD_1080' )

    #find the shot with exr file(part of lighting step)
    res = findShots(selecFilter=exrFilter,seq=seq,taskname=taskname)

    #if user just want to see the anim in the contact sheet
    if not lightOnly:
        lightingShotFound = []
        for shot in res.keys():
            lightingShotFound.append(shot)
        if len(lightingShotFound) is 0:
            lightingShotFound.append('Not')
        resAnim = findShots(selecFilter=animFilter,seq=seq,taskname='anim_main',shotList=lightingShotFound)
        resAnim.update(res)
        res = resAnim

    #create the main dict
    shotPath= createShotPathDict(res=res,shotFrame=shotFrame)

    #find the directory where to put the output files
    fileOutPath = createFileOutput(path = _OUTPATH_, seq = seq)

    #number of shot in exr for averaging color
    exrShot = 0
    for shot in res:
        if shotPath[shot]['imageFormat'] == '.exr':
            exrShot+=1
    #number of shot in sequence
    nbShot = len(shotPath.keys())
    #height of contact sheet
    heightContactSheet = (int(nbShot/nbColumns)+1)*1170
    #width of contactsheet
    widthContactSheet = 1920*nbColumns
    #average color for the shot
    averageColor=[]
    #average color for sequence
    totalAvColor=[0.0,0.0,0.0,1]
    # X/Y pos for nodes
    Xpos = 0
    Ypos = 0
    # size of the color swath in the roto node
    sizeSquare = widthContactSheet/nbShot
    if sizeSquare > 500:
        sizeSquare = 500
    # shift for the color swatch
    shiftX = 0
    # input of the contactsheet
    input = 0
    #max and min cut for the sequence
    maxCutOut = 0
    minCutIn = 101

    #variable for HD presentation (i.e contactSheet separated if nbShots > 30
    nbContactSheetHD = 0
    contactSheetHD= []
    nbRowHD=4
    nbColumnsHD = 6
    colTimeRow = nbColumnsHD * nbRowHD
    heightContactSheetHD = nbRowHD * 1170
    widthContactSheetHD = nbColumnsHD * 1920
    if nbShot > colTimeRow:
        nbContactSheetHD = float(nbShot)/float(colTimeRow)
        frac, whole = math.modf(nbContactSheetHD)
        if frac > 0:
            nbContactSheetHD = int(whole + 1)
        else:
            nbContactSheetHD= int(nbContactSheetHD)


    #creation of the roto Node
    rotoNode = nuke.nodes.Roto(name = 'roto',cliptype="no clip")
    rCurves = rotoNode['curves']
    root = rCurves.rootLayer

    #creation of the contactsheet node
    contactSheetNode = nuke.nodes.ContactSheet(name="contactSheet",rows=int(nbShot/nbColumns)+1,columns=nbColumns,roworder="TopBottom",width=widthContactSheet,height=heightContactSheet, center= True,gap = 50)

    #reformat node for the contact sheet
    reformatGlobalNode = nuke.nodes.Reformat(type = "to box",box_fixed = True,resize = "none",box_width = widthContactSheet, box_height = heightContactSheet+2160,black_outside = True,name = "reformatGlobal")
    #text node displaying the sequence number
    textSeqNode = nuke.nodes.Text2(message=seq,cliptype="no clip",global_font_scale=8.5,name="title"+seq)
    textSeqNode["box"].setValue([0,0,2500,1080])
    textSeqNode["font"].setValue('Captain Underpants', 'Regular')
    textSeqNodeTransform = nuke.nodes.Transform(name = "transformSeq_"+seq)
    textSeqNodeTransform['translate'].setValue([200,heightContactSheet+900])
    textSeqNodeTransform.setInput(0,textSeqNode)
    #reformat for the roto node the height is the height of a swatch node
    reformatColAverage = nuke.nodes.Reformat(type="to box",box_fixed=True,resize="none",box_width=widthContactSheet,box_height=sizeSquare,center=False,pbb=True,name="reformatColAverage")
    #constant color for average sequence color
    constantNode = nuke.nodes.Constant(name="averageSeqColor")
    constantNodeTransform = nuke.nodes.Transform(name = "transformConst_"+seq,scale = 0.6)
    constantNodeTransform['translate'].setValue([widthContactSheet-(1920*2),heightContactSheet+1200])
    constantNodeTransform.setInput(0,constantNode)
    #import of the colorChart
    readColorChartNode = nuke.nodes.Read(file="/s/prods/captain/_sandbox/duda/images/sRGBtoSpi_ColorCheckerMikrosWrongColor.exr",name=seq+"_colorChart")
    readColorChartNodeTransform = nuke.nodes.Transform(name = "transformChart_"+seq,scale = 0.85)
    readColorChartNodeTransform['translate'].setValue([widthContactSheet-(1920),heightContactSheet+1080])
    readColorChartNodeTransform.setInput(0,readColorChartNode)

    #merge of all the nodes
    mergeNode = nuke.nodes.Merge2(inputs=[reformatGlobalNode,textSeqNodeTransform],name="merge_"+seq)
    mergeNode.setInput(3,readColorChartNodeTransform)
    mergeNode.setInput(4,reformatColAverage)
    mergeNode.setInput(5,constantNodeTransform)

    #write node
    writeFullNode = nuke.nodes.Write(name = seq + "Write", colorspace = "linear", file_type = "exr",file =fileOutPath["EXR"] )
    writeFullLutBurnNode = nuke.nodes.Write(name = seq + "WriteLutBurn", colorspace = "linear", file_type = "jpeg", _jpeg_sub_sampling = "4:2:2",file =fileOutPath["JPG"])
    writeFullLutBurnNode['_jpeg_quality'].setValue(0.75)
    writeHDNode = nuke.nodes.Write(name = seq + "WriteHD", colorspace = "linear", file_type = "jpeg", _jpeg_sub_sampling = "4:2:2",file =fileOutPath["HD"])
    writeHDNode['_jpeg_quality'].setValue(0.75)
    writeMovieNode = nuke.nodes.Write(name = seq + "WriteMovie", colorspace = "linear", file_type = "mov",file =fileOutPath["Movie"])
    colorConvertNode = nuke.nodes.OCIOColorSpace(in_colorspace="linear",out_colorspace="vd")
    reformatWriteHDNode = nuke.nodes.Reformat(type="to format",resize="fit",center=True,black_outside = True,name="reformatHD_"+seq)
    writeFullLutBurnNode.setInput(0,colorConvertNode)
    writeMovieNode.setInput(0,reformatWriteHDNode)
    colorConvertNode.setInput(0,mergeNode)
    writeFullNode.setInput(0,mergeNode)
    reformatWriteHDNode.setInput(0,colorConvertNode)
    writeHDNode.setInput(0,reformatWriteHDNode)

    for path in sorted(shotPath.keys()):
        frameNumber =[]
        cutIn, cutOut, cutMid = shotPath[path]['in'], shotPath[path]['out'],shotPath[path]['mid']
        frameNumber = shotPath[path]['averageFrame']
        textColor = [1,1,1,1]
        if cutOut > maxCutOut:
            maxCutOut = cutOut
        if cutIn < minCutIn:
            minCutIn = cutIn
        #get the average color only for the shot with exr image
        if shotPath[path]['imageFormat'] == '.exr':
            averageColor =getAvrageColor(frameNumber=frameNumber, frame=shotPath[path]['rootFrame'])
            totalAvColor[0]+=averageColor[0]
            totalAvColor[1]+=averageColor[1]
            totalAvColor[2]+=averageColor[2]
        #else if it's coming from anim_main just put black
        else:
            averageColor = [0,0,0]
        readNode = nuke.nodes.Read(file = shotPath[path]['frame'],first=cutIn,last=cutOut, name = "read_"+path,on_error ='nearestframe',after='loop')
        readNode.setXYpos(Xpos, Ypos)
        width = readNode.metadata("input/width")

        shape =rp.Shape(rCurves,type='bezier')
        shape.append([shiftX,sizeSquare])
        shape.append([shiftX + sizeSquare,sizeSquare])
        shape.append([shiftX + sizeSquare,0])
        shape.append([shiftX,0])
        shape.name = 'shape_'+path
        shapeAttr = shape.getAttributes()
        shapeAttr.set('r',averageColor[0])
        shapeAttr.set('g',averageColor[1])
        shapeAttr.set('b',averageColor[2])
        root.append(shape)

        reformatNode = nuke.nodes.Reformat(type = "to box",box_fixed = True,resize = "none",box_width = 1920, box_height = 1170,black_outside = True,name = "reformat_" + path)
        reformatNode.setInput(0,readNode)
        reformatNode.setXYpos(Xpos, Ypos +90)
        transformNode = nuke.nodes.Transform(name = "transform_"+path)
        transformNode['translate'].setValue([0,-45])
        transformNode.setXYpos(Xpos, Ypos +120)
        transformNode.setInput(0,reformatNode)
        if shotPath[path]['imageFormat'] == '.exr':
            if shotPath[path]['status'] == 'cmpt':
                textColor = [0,1,0,1]
        textNode = nuke.nodes.Text2(message=path + "    Task: " + shotPath[path]['task'] + "    Version: " + shotPath[path]['version'],cliptype="no clip",global_font_scale=.8,name="title"+path)
        textNode["box"].setValue([25,1050,1920,1160])
        textNode['color'].setValue(textColor)
        textNode["font"].setValue('Captain Underpants', 'Regular')
        textNode.setInput(0,transformNode)
        textNode.setXYpos(Xpos, Ypos +150)
        contactSheetNode.setInput(input,textNode)
        input+=1
        Xpos += 125
        shiftX += sizeSquare

    #set the average color for the sequence in the constant node
    if exrShot is not 0:
        avCol = [totalAvColor[0]/exrShot,totalAvColor[1]/exrShot,totalAvColor[2]/exrShot,1]
        constantNode['color'].setValue(avCol)


    #if the user want multiple frames of contactSheet
    if HDsplit and nbShot > colTimeRow :
        inputContactSheet = 0
        contactSheetNumber = 0
        for i in range(nbContactSheetHD):
            contactSheetNodeHD = nuke.nodes.ContactSheet(name="contactSheet"+str(i),rows=nbRowHD,columns=nbColumnsHD,roworder="TopBottom",width=widthContactSheetHD,height=heightContactSheetHD, center= True,gap = 50)
            contactSheetNodeHD["hide_input"].setValue(True)
            contactSheetHD.append(contactSheetNodeHD )
        for item in sorted(shotPath.keys()):
            node = nuke.toNode('title'+item)
            contactSheetHD[contactSheetNumber].setInput(inputContactSheet,node)
            inputContactSheet += 1
            if inputContactSheet > colTimeRow:
                inputContactSheet = 0
                contactSheetNumber += 1
        appendClipNodeContactSheetHD = nuke.nodes.AppendClip(name = "appendClipNodeContactSheetHD_"+seq)
        inputContactSheet = 0
        for node in contactSheetHD:
            appendClipNodeContactSheetHD.setInput(inputContactSheet,node)
            inputContactSheet+=1

        readColorChartNodeTransformHD = nuke.nodes.Transform(name = "transformChartHD_"+seq,scale = 0.85)
        readColorChartNodeTransformHD['translate'].setValue([widthContactSheetHD-(1920),heightContactSheetHD+1080])
        readColorChartNodeTransformHD.setInput(0,readColorChartNode)

        textSeqNodeTransformHD = nuke.nodes.Transform(name = "transformSeqHD_"+seq)
        textSeqNodeTransformHD['translate'].setValue([200,heightContactSheetHD+900])
        textSeqNodeTransformHD.setInput(0,textSeqNode)

        constantNodeTransformHD = nuke.nodes.Transform(name = "transformConstHD_"+seq,scale = 0.6)
        constantNodeTransformHD['translate'].setValue([widthContactSheetHD-(1920*2),heightContactSheetHD+1200])
        constantNodeTransformHD.setInput(0,constantNode)

        reformatColAverageHD = nuke.nodes.Reformat(type="to box",box_fixed=True,resize="none",box_width=widthContactSheetHD,box_height=sizeSquare,center=False,pbb=True,name="reformatColAverageHD")
        reformatColAverageHD.setInput(0,rotoNode)

        reformatGlobalNodeHD = nuke.nodes.Reformat(type = "to box",box_fixed = True,resize = "none",box_width = widthContactSheetHD, box_height = heightContactSheetHD+2160,black_outside = True,name = "reformatGlobalHD")
        reformatGlobalNodeHD.setInput(0,appendClipNodeContactSheetHD)

        mergeNodeHD = nuke.nodes.Merge2(inputs=[reformatGlobalNodeHD,textSeqNodeTransformHD],name="merge_"+seq)
        mergeNodeHD.setInput(3,readColorChartNodeTransformHD)
        mergeNodeHD.setInput(4,reformatColAverageHD)
        mergeNodeHD.setInput(5,constantNodeTransformHD)
        #mergeNodeHD["hide_input"].setValue(True)

        pageNumberNodeHD = nuke.nodes.Text2(cliptype="no clip",global_font_scale=3,name="pageNumberHD_"+seq)
        pageNumberNodeHD.setInput(0,mergeNodeHD)
        pageNumberNodeHD["box"].setValue([9576,280,12345,890])
        pageNumberNodeHD["font"].setValue('Captain Underpants', 'Regular')
        pageNumberNodeHD["message"].setValue("Page: [frame]/"+str(nbContactSheetHD))

        colorConvertNodeHD = nuke.nodes.OCIOColorSpace(in_colorspace="linear",out_colorspace="vd")
        colorConvertNodeHD.setInput(0,pageNumberNodeHD)

        reformatWriteHDNodeHD = nuke.nodes.Reformat(type="to format",resize="fit",center=True,black_outside = True,name="reformatHD_"+seq)
        reformatWriteHDNodeHD.setInput(0,colorConvertNodeHD)
        writeHDNode = nuke.nodes.Write(name = seq + "WriteHD", colorspace = "linear", file_type = "mov",file =fileOutPath["HD"],mov64_codec='Avid DNxHD Codec',mov64_dnxhd_codec_profile='DNxHD 422 10-bit 220Mbit')
        writeHDNode.setInput(0,reformatWriteHDNodeHD)

        centerXHD = Xpos/2 -600
        shiftX = -125
        for item in contactSheetHD:
            newXPos = shiftX + abs(contactSheetHD.index(item)*shiftX)
            item.setXYpos(centerXHD+newXPos,700)
        appendClipNodeContactSheetHD.setXYpos(centerXHD,750)
        reformatColAverageHD.setXYpos(centerXHD-shiftX,750)
        reformatGlobalNodeHD.setXYpos(centerXHD,800)
        textSeqNodeTransformHD.setXYpos(centerXHD-shiftX,800)
        readColorChartNodeTransformHD.setXYpos(centerXHD+shiftX,800)
        mergeNodeHD.setXYpos(centerXHD,850)
        pageNumberNodeHD.setXYpos(centerXHD,900)
        colorConvertNodeHD.setXYpos(centerXHD,950)
        reformatWriteHDNodeHD.setXYpos(centerXHD,1000)
        writeHDNode.setXYpos(centerXHD,1050)

    #connection and position of the nodes for the comp
    centerX = Xpos/2
    reformatGlobalNode.setInput(0,contactSheetNode)
    contactSheetNode.setXYpos(centerX, 700)
    reformatColAverage.setInput(0,rotoNode)
    reformatColAverage.setXYpos((centerX)-200, 800)
    rotoNode.setXYpos((centerX)-200, 750)
    reformatGlobalNode.setXYpos(centerX, 750)
    textSeqNode.setXYpos((centerX)+200, 750)
    textSeqNodeTransform.setXYpos((centerX)+200, 800)
    readColorChartNode.setXYpos((centerX)+400, 700)
    readColorChartNodeTransform.setXYpos((centerX)+400, 800)
    constantNode.setXYpos(centerX+600, 700)
    constantNodeTransform.setXYpos((centerX)+600, 800)
    mergeNode.setXYpos(centerX, 850)
    colorConvertNode.setXYpos(centerX + 200, 950)
    writeFullNode.setXYpos(centerX, 1050)
    writeFullLutBurnNode.setXYpos(centerX + 200, 1050)
    reformatWriteHDNode.setXYpos(centerX + 400, 1000)
    if not HDsplit:
        writeHDNode.setXYpos(centerX + 400, 1050)
    writeMovieNode.setXYpos(centerX + 600, 1050)

    #render the frame
    if render:
        nuke.execute(writeFullNode,1,1)
        nuke.execute(writeFullLutBurnNode,1,1)
        if not HDsplit or nbShot < colTimeRow:
            nuke.execute(writeHDNode,1,1)
        else:
            nuke.execute(writeHDNode,1,nbContactSheetHD)

    if display:
        HDpath = fileOutPath["HD"][:fileOutPath["HD"].find(".")]+'*'
        commandLine = "rv "+ HDpath
        os.system(commandLine)

#get the arg from user
def get_args():
    #Assign description to the help doc
    parser = argparse.ArgumentParser(description = "create a contactSheet for sequence or contactSheet for masters")
    #shot argument
    parser.add_argument('--sq','-sq', type=str, help='seq number')
    parser.add_argument('--f','-f',type=str, help='frame to displat can be "start", "mid" or "end"')
    parser.add_argument('--sh','-sh', nargs = '*', dest = 'shots', type=str, help='shot(s) for master to find')
    parser.add_argument('--task','-task',type=str, help='task to grab the images')
    parser.add_argument('--l','-l', action='store_true', help='just calculate the contactSheet with the lighted images')
    parser.add_argument('--M','-M',action='store_true', help='switch in master mode')
    parser.add_argument('--noRender','-noRender',action='store_false', help='do not render the files')
    parser.add_argument('--showML','-showML',action='store_true', help='display the name of masters in sequence')
    parser.add_argument('--mn','-mn', type=str, help='master name')
    parser.add_argument('--d','-d',action='store_true', help='display the images')
    parser.add_argument('--HDsplit','-HDsplit',action='store_true', help='display the images')
    args = parser.parse_args()
    seqNumber = args.sq
    if seqNumber.find('s') < 0:
        seqNumber = "s"+ seqNumber.zfill(4)
    shotNumber = args.shots
    if shotNumber is not None and len(shotNumber)>0:
        formatName = []
        for shot in shotNumber:
            formatName.append(seqNumber+'_p'+shot.zfill(5))
            shotNumber = formatName
    task = args.task
    mastersInSeq = args.showML
    lightOn = args.l
    masterNumber = args.mn
    masterOn = args.M
    frameChosen = args.f
    renderOn = args.noRender
    displayOn = args.d
    HDsplit = args.HDsplit
    return seqNumber, frameChosen, task, lightOn, masterNumber, masterOn, renderOn, mastersInSeq, shotNumber, displayOn, HDsplit


def main():
    seqNumber, frameChosen, task, lightOn, masterNumber, masterOn, renderOn,mastersInSeq,shotNumber, displayOn, HDsplit = get_args()
    #if user just want to list what are the master name in the sequence
    if mastersInSeq:
        masters = findMasters(seq=seqNumber)
        for key in masters:
            print '\n'+ key
            for shot in masters[key]['sortedShot']:
                print '\t'+ shot
    #if user want to enter a shot(s) to find the cannected master
    elif shotNumber is not None and len(shotNumber)>0:
        findMasterFromShot(seq=seqNumber,shotList = shotNumber)

    else:
        if task is None:
            task = 'compo_precomp'
        #creating master contactSheet
        if masterOn:
            if masterNumber is None:
                createContactSheetMasters(shotFrame = frameChosen,nbColumns = 6,seq =seqNumber,taskname=task,lightOnly = lightOn, master='All',render=renderOn,display=displayOn)
            else:
                createContactSheetMasters(shotFrame = frameChosen,nbColumns = 6,seq =seqNumber,taskname=task,lightOnly = lightOn, master=masterNumber,render=renderOn,display=displayOn)
        #creating sequence contactSheet
        else:
            createContactSheetAllSequence(shotFrame = frameChosen,nbColumns = 6,seq =seqNumber,taskname=task,lightOnly = lightOn,render=renderOn, display = displayOn, HDsplit=HDsplit)

#create a contactsheet of all the masters in the sequence
def createMastersContactForSeq(shotFrame = 'start',nbColumns = 6,seq ="s0300",taskname='compo_precomp',lightOnly = False,render= True, display = False):
    import nuke
    import nuke.rotopaint as rp
    root = nuke.root()
    root['format'].setValue( 'HD_1080' )
    Xpos = 0
    Ypos =0
    commandline = "rv "
    #find the masters for the sequence
    mastersSeq = findMasters(seq=seq)
    mastersList =[]
    for key in mastersSeq:
        mastersList.append(mastersSeq[key]['masterShot'])
    #find the shot with exr file(part of lighting step)
    res = findShots(selecFilter=exrFilter,seq=seq,taskname=taskname)
    #if user want to see the anim in the contact sheet
    if not lightOnly:
        lightingShotFound = []
        for shot in res.keys():
            lightingShotFound.append(shot)
        resAnim = findShots(selecFilter=animFilter,seq=seq,taskname='anim_main',shotList=lightingShotFound)
        resAnim.update(res)
        res = resAnim

    #take the shot who are not Masters out of the dictionary
    for shot in res.keys():
        if shot not in mastersList:
            res.pop(shot)
    #create the main dict
    shotPath= createShotPathDict(res=res,shotFrame=shotFrame)

    #find the directory where to put the output files
    fileOutPath = createFileOutput(path = _OUTPATH_, seq = seq,createMasterGlobSeq=True)

    #number of shot in exr for averaging color
    exrShot = 0
    for shot in res:
        if shotPath[shot]['imageFormat'] == '.exr':
            exrShot+=1
    #number of shot in sequence
    nbShot = len(shotPath.keys())
    #height of contact sheet
    heightContactSheet = (int(nbShot/nbColumns)+1)*1170
    #width of contactsheet
    widthContactSheet = 1920*nbColumns
    #average color for the shot
    averageColor=[]
    #average color for sequence
    totalAvColor=[0.0,0.0,0.0,1]
    # X/Y pos for nodes
    Xpos = 0
    Ypos = 0
    # size of the color swath in the roto node
    sizeSquare = widthContactSheet/nbShot
    if sizeSquare > 500:
        sizeSquare = 500
    # shift for the color swatch
    shiftX = 0
    # input of the contactsheet
    input = 0
    #max and min cut for the sequence
    maxCutOut = 0
    minCutIn = 101

    #creation of the roto Node
    rotoNode = nuke.nodes.Roto(name = 'roto',cliptype="no clip")
    rCurves = rotoNode['curves']
    root = rCurves.rootLayer

    #creation of the contactsheet node
    contactSheetNode = nuke.nodes.ContactSheet(name="contactSheet",rows=int(nbShot/nbColumns)+1,columns=nbColumns,roworder="TopBottom",width=widthContactSheet,height=heightContactSheet, center= True,gap = 50)

    #reformat node for the contact sheet
    reformatGlobalNode = nuke.nodes.Reformat(type = "to box",box_fixed = True,resize = "none",box_width = widthContactSheet, box_height = heightContactSheet+2160,black_outside = True,name = "reformatGlobal")
    #text node displaying the sequence number
    textSeqNode = nuke.nodes.Text2(message=seq+ " Masters",cliptype="no clip",global_font_scale=8.5,name="title"+seq)
    textSeqNode["box"].setValue([0,0,5710,1080])
    textSeqNode["font"].setValue('Captain Underpants', 'Regular')
    textSeqNodeTransform = nuke.nodes.Transform(name = "transformSeq_"+seq)
    textSeqNodeTransform['translate'].setValue([200,heightContactSheet+900])
    textSeqNodeTransform.setInput(0,textSeqNode)
    #reformat for the roto node the height is the height of a swatch node
    reformatColAverage = nuke.nodes.Reformat(type="to box",box_fixed=True,resize="none",box_width=widthContactSheet,box_height=sizeSquare,center=False,pbb=True,name="reformatColAverage")
    #constant color for average sequence color
    constantNode = nuke.nodes.Constant(name="averageSeqColor")
    constantNodeTransform = nuke.nodes.Transform(name = "transformConst_"+seq,scale = 0.6)
    constantNodeTransform['translate'].setValue([widthContactSheet-(1920*2),heightContactSheet+1200])
    constantNodeTransform.setInput(0,constantNode)
    #import of the colorChart
    readColorChartNode = nuke.nodes.Read(file="/s/prods/captain/_sandbox/duda/images/sRGBtoSpi_ColorCheckerMikrosWrongColor.exr",name=seq+"_colorChart")
    readColorChartNodeTransform = nuke.nodes.Transform(name = "transformChart_"+seq,scale = 0.85)
    readColorChartNodeTransform['translate'].setValue([widthContactSheet-(1920),heightContactSheet+1080])
    readColorChartNodeTransform.setInput(0,readColorChartNode)

    #merge of all the nodes
    mergeNode = nuke.nodes.Merge2(inputs=[reformatGlobalNode,textSeqNodeTransform],name="merge_"+seq)
    mergeNode.setInput(3,readColorChartNodeTransform)
    mergeNode.setInput(4,reformatColAverage)
    mergeNode.setInput(5,constantNodeTransform)

    #write node
    writeFullNode = nuke.nodes.Write(name = seq + "Write", colorspace = "linear", file_type = "exr",file =fileOutPath["EXR"] )
    writeFullLutBurnNode = nuke.nodes.Write(name = seq + "WriteLutBurn", colorspace = "linear", file_type = "jpeg", _jpeg_sub_sampling = "4:2:2",file =fileOutPath["JPG"])
    writeFullLutBurnNode['_jpeg_quality'].setValue(0.75)
    writeHDNode = nuke.nodes.Write(name = seq + "WriteHD", colorspace = "linear", file_type = "jpeg", _jpeg_sub_sampling = "4:2:2",file =fileOutPath["HD"])
    writeHDNode['_jpeg_quality'].setValue(0.75)
    writeMovieNode = nuke.nodes.Write(name = seq + "WriteMovie", colorspace = "linear", file_type = "mov",file =fileOutPath["Movie"])
    colorConvertNode = nuke.nodes.OCIOColorSpace(in_colorspace="linear",out_colorspace="vd")
    reformatWriteHDNode = nuke.nodes.Reformat(type="to format",resize="fit",center=True,black_outside = True,name="reformatHD_"+seq)
    writeFullLutBurnNode.setInput(0,colorConvertNode)
    writeMovieNode.setInput(0,reformatWriteHDNode)
    colorConvertNode.setInput(0,mergeNode)
    writeFullNode.setInput(0,mergeNode)
    reformatWriteHDNode.setInput(0,colorConvertNode)
    writeHDNode.setInput(0,reformatWriteHDNode)

    for path in sorted(shotPath.keys()):
        frameNumber =[]
        cutIn, cutOut, cutMid = shotPath[path]['in'], shotPath[path]['out'],shotPath[path]['mid']
        frameNumber = shotPath[path]['averageFrame']
        textColor = [1,1,1,1]
        if cutOut > maxCutOut:
            maxCutOut = cutOut
        if cutIn < minCutIn:
            minCutIn = cutIn
        #get the average color only for the shot with exr image
        if shotPath[path]['imageFormat'] == '.exr':
            averageColor =getAvrageColor(frameNumber=frameNumber, frame=shotPath[path]['rootFrame'])
            totalAvColor[0]+=averageColor[0]
            totalAvColor[1]+=averageColor[1]
            totalAvColor[2]+=averageColor[2]
        #else if it's coming from anim_main just put black
        else:
            averageColor = [0,0,0]
        readNode = nuke.nodes.Read(file = shotPath[path]['frame'],first=cutIn,last=cutOut, name = "read_"+path,on_error ='nearestframe',after='loop')
        readNode.setXYpos(Xpos, Ypos)
        width = readNode.metadata("input/width")

        shape =rp.Shape(rCurves,type='bezier')
        shape.append([shiftX,sizeSquare])
        shape.append([shiftX + sizeSquare,sizeSquare])
        shape.append([shiftX + sizeSquare,0])
        shape.append([shiftX,0])
        shape.name = 'shape_'+path
        shapeAttr = shape.getAttributes()
        shapeAttr.set('r',averageColor[0])
        shapeAttr.set('g',averageColor[1])
        shapeAttr.set('b',averageColor[2])
        root.append(shape)

        reformatNode = nuke.nodes.Reformat(type = "to box",box_fixed = True,resize = "none",box_width = 1920, box_height = 1170,black_outside = True,name = "reformat_" + path)
        reformatNode.setInput(0,readNode)
        reformatNode.setXYpos(Xpos, Ypos +90)
        transformNode = nuke.nodes.Transform(name = "transform_"+path)
        transformNode['translate'].setValue([0,-45])
        transformNode.setXYpos(Xpos, Ypos +120)
        transformNode.setInput(0,reformatNode)
        if shotPath[path]['imageFormat'] == '.exr':
            if shotPath[path]['status'] == 'cmpt':
                textColor = [0,1,0,1]
        textNode = nuke.nodes.Text2(message=path + "    Task: " + shotPath[path]['task'] + "    Version: " + shotPath[path]['version'],cliptype="no clip",global_font_scale=.8,name="title"+path)
        textNode["box"].setValue([25,1050,1920,1160])
        textNode['color'].setValue(textColor)
        textNode["font"].setValue('Captain Underpants', 'Regular')
        textNode.setInput(0,transformNode)
        textNode.setXYpos(Xpos, Ypos +150)
        contactSheetNode.setInput(input,textNode)
        input+=1
        Xpos += 125
        shiftX += sizeSquare

    #set the average color for the sequence in the constant node
    if exrShot is not 0:
        avCol = [totalAvColor[0]/exrShot,totalAvColor[1]/exrShot,totalAvColor[2]/exrShot,1]
        constantNode['color'].setValue(avCol)

    #connection and position of the nodes for the comp
    centerX = Xpos/2
    reformatGlobalNode.setInput(0,contactSheetNode)
    contactSheetNode.setXYpos(centerX, 700)
    reformatColAverage.setInput(0,rotoNode)
    reformatColAverage.setXYpos((centerX)-200, 800)
    rotoNode.setXYpos((centerX)-200, 750)
    reformatGlobalNode.setXYpos(centerX, 750)
    textSeqNode.setXYpos((centerX)+200, 750)
    textSeqNodeTransform.setXYpos((centerX)+200, 800)
    readColorChartNode.setXYpos((centerX)+400, 700)
    readColorChartNodeTransform.setXYpos((centerX)+400, 800)
    constantNode.setXYpos(centerX+600, 700)
    constantNodeTransform.setXYpos((centerX)+600, 800)
    mergeNode.setXYpos(centerX, 850)
    colorConvertNode.setXYpos(centerX + 200, 950)
    writeFullNode.setXYpos(centerX, 1050)
    writeFullLutBurnNode.setXYpos(centerX + 200, 1050)
    reformatWriteHDNode.setXYpos(centerX + 400, 1000)
    writeHDNode.setXYpos(centerX + 400, 1050)
    writeMovieNode.setXYpos(centerX + 600, 1050)

    #render the frame
    if render:
        nuke.execute(writeFullNode,1,1)
        nuke.execute(writeFullLutBurnNode,1,1)
        nuke.execute(writeHDNode,1,1)

    if display:
        HDpath = fileOutPath["HD"][:fileOutPath["HD"].find(".")]+'*'
        commandline = "rv "+ HDpath
        os.system(commandline )

    print minCutIn, maxCutOut


#if __name__== '__main__': main()




#createContactSheetAllSequence('mid',nbColumns = 6,seq ="s1300",taskname='compo_precomp',lightOnly = False,HDsplit=True,render=True)
#createContactSheetMasters(shotFrame = 'start',nbColumns = 6,seq ="s0300",taskname='compo_precomp',lightOnly = False, master='All')
#createMastersContactForSeq(shotFrame = 'start',nbColumns = 6,seq ="s1300",taskname='compo_precomp',lightOnly = False,render= False, display = False)
