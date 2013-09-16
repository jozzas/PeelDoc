#! /usr/bin/python

"""
PeelDoc v0.1 adapted from HyperSQL v1.0 by Randy Phillips.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

Author contact information: jozzas@gmail.com
"""
#FIXME: Fix function name Capitalisation
#FIXME: Create a config file
#FIXME: Create a html_template file
#FIXME: Create a standalone CSS file that is copied into output directories
#FIXME: Fix indentation

# Real to do list:
#  - Add comments from above each package / procedure definition
#  - tidy up code - some procedures are epic! (not my ones)

import os, sys, string, time

class ViewInfo:
  def __init__(self):
    self.viewName = ""
    self.lineNumber = -1
    self.whereUsed = {} # file name key, fileInfo and line number list
    self.uniqueNumber = 0 # used to create unique file name for where used list
    self.parent = None

class FunctionInfo:
  def __init__(self):
    self.functionName = ""
    self.lineNumber = -1
    self.whereUsed = {} # file name key, fileInfo and line number list
    self.uniqueNumber = 0 # used to create unique file name for where used list
    self.parent = None

class ProcedureInfo:
  def __init__(self):
    self.procedureName = ""
    self.lineNumber = -1
    self.whereUsed = {} # file name key, fileInfo and line number list
    self.uniqueNumber = 0 # used to create unique file name for where used list
    self.parent = None

class PackageInfo:
  def __init__(self):
    self.packageName = ""
    self.lineNumber = -1
    self.functionInfoList = []
    self.procedureInfoList = []
    self.whereUsed = {} # file name key, fileInfo and line number list
    self.uniqueNumber = 0 # used to create unique file name for where used list
    self.parent = None

class FileInfo:
  def __init__(self):
    self.fileName = ""
    self.fileType = "" # cpp files are only scanned for sql "where used" information
    self.viewInfoList = []
    self.packageInfoList = []
    self.uniqueNumber = 0 # used to create unique file name for where used list

class MetaInfo:
  def __init__(self):
    self.fileInfoList = []
    self.fileWithPathnamesIndex_FileName = ""
    self.fileNoPathnamesIndex_FileName = ""
    self.viewIndex_FileName = ""
    self.packageIndex_FileName = ""
    self.functionIndex_FileName = ""
    self.procedureIndex_FileName = ""
    self.packageFuncProdIndex_FileName = ""
    self.scriptName = ""
    self.htmlDir = ""
    self.versionString = ""
    self.toDoList = ""
    self.indexForWhereUsedFiles = 0

  def NextIndex(self):
    """Generate unique index number for 'where used' indices"""
    self.indexForWhereUsedFiles += 1
    return self.indexForWhereUsedFiles

def TupleCompareFirstElements(a, b):
  """ used for sorting list of tuples by values of first elements in the tuples"""
  if a[0] < b[0]:
    return -1
  if a[0] > b[0]:
    return 1
  return 0


def CaseInsensitiveComparison(a, b):
  """ used for case insensitive string sorts"""
  if a.upper() < b.upper():
    return -1
  if a.upper() > b.upper():
    return 1
  return 0


def FindFilesAndBuildFileList(dir, fileInfoList, meta_info):
  # get a list of this directory's contents
  # these items are relative and not absolute
  names=os.listdir(dir)
    
  for i in names:
    if (i == "RCS") or (i == "old_directories") or (i == ".svn"):
        # do not look in these directories
        continue

    f1=os.path.join(dir, i)     # convert from relative to absolute addressing

    if os.path.isdir(f1): #recurse this too
      FindFilesAndBuildFileList(f1, fileInfoList, meta_info)

    # file found, only add specific file extensions to the list
    else:
      if f1[len(f1)-4:] == ".sql" or f1[len(f1)-4:] == ".bdy" or f1[len(f1)-3:] == ".qf" or f1[len(f1)-4:] == ".pls":
          temp = FileInfo()
          temp.fileName = f1
          temp.fileType = "sql"
          if temp.uniqueNumber == 0:
              temp.uniqueNumber = meta_info.NextIndex()
              fileInfoList.append(temp)
              meta_info.fileCount += 1
              
  print str(len(fileInfoList)) + " files found"


def ScanFilesForViewsAndPackages(meta_info):
    fileInfoList = meta_info.fileInfoList

    dot_count = 1
    for file_info in fileInfoList:

        # skip all non-sql files
        if file_info.fileType != "sql":
            continue
        
        # print a . every file
        sys.stdout.write(".")
        sys.stdout.flush()
        if (dot_count % 60) == 0: # carriage return every 60 dots
            print
            sys.stdout.flush()
        dot_count += 1
        
        infile = open(file_info.fileName, "r")
        fileLines = infile.readlines()
        infile.close()

        # if we find a package definition, this flag tells us to also look for
        # functions and procedures.  If we don't find a package definition, there
        # is no reason to look for them
        package_count = -1

        for lineNumber in range(len(fileLines)):

            token_list = fileLines[lineNumber].split()

            # ignore very short lines
            if len(token_list) < 2:
                continue

            # ignore lines that begin with comments
            if token_list[0][:2] == "--" or token_list[0][:2] == "//" or token_list[0][:2] == "##":
                continue

            # find views.  Loop through looking for the different styles of view definition
            for token_index in range(len(token_list)):
                # look for CREATE VIEW, REPLACE VIEW, FORCE VIEW, making sure enough tokens exist
                if len(token_list) > token_index+1:
                    if token_list[token_index+1].upper() == "VIEW" \
                    and (token_list[token_index].upper() == "CREATE" \
                    or token_list[token_index].upper() == "REPLACE" \
                    or token_list[token_index].upper() == "FORCE"):
                      view_info = ViewInfo()
                      view_info.parent = file_info
                      view_info.viewName = token_list[token_index+2]
                      view_info.lineNumber = lineNumber
                      file_info.viewInfoList.append(view_info)
                      

            # find package definitions - set flag if found
            # look for PACKAGE BODY x, making sure enough tokens exist
            for token_index in range(len(token_list)):
                if len(token_list) > token_index+2:
                    if token_list[token_index].upper() == "PACKAGE":
                        if token_list[token_index+1].upper() == "BODY":
                            package_info = PackageInfo()
                            package_info.parent = file_info
                            package_info.packageName = token_list[token_index+2]
                            package_info.lineNumber = lineNumber
                            file_info.packageInfoList.append(package_info) # permanent storage
                            package_count += 1 # use this flag below
            
            # if a package definition was found, look for functions and procedures
            if package_count != -1:
                # first find functions
                if len(token_list) > 1 and token_list[0].upper() == "FUNCTION":
                    function_name = token_list[1].split('(')[0] # some are "name(" and some are "name ("
                    function_info = FunctionInfo()
                    function_info.parent = file_info.packageInfoList[package_count]
                    function_info.functionName = function_name
                    function_info.lineNumber = lineNumber
                    file_info.packageInfoList[package_count].functionInfoList.append(function_info)
            
                # now find procedures
                if len(token_list) > 1 and token_list[0].upper() == "PROCEDURE":
                    procedure_name = token_list[1].split('(')[0] # some are "name(" and some are "name ("
                    procedure_info = ProcedureInfo()
                    procedure_info.parent = file_info.packageInfoList[package_count]
                    procedure_info.procedureName = procedure_name
                    procedure_info.lineNumber = lineNumber
                    file_info.packageInfoList[package_count].procedureInfoList.append(procedure_info)


def ScanFilesForWhereViewsAndPackagesAreUsed(meta_info):
    fileInfoList = meta_info.fileInfoList

    outerfileInfoList = []
    for file_info in fileInfoList:
        outerfileInfoList.append(file_info)

    dot_count = 1
    for outer_file_info in outerfileInfoList:
        # print a . every file
        sys.stdout.write(".")
        sys.stdout.flush()
        if (dot_count % 60) == 0: # carriage return every 60 dots
            print
            sys.stdout.flush()
        dot_count += 1
    
        infile = open(outer_file_info.fileName, "r")
        fileLines = infile.readlines()
        infile.close()

        # if we find a package definition, this flag tells us to also look for
        # functions and procedures.  If we don't find a package definition, there
        # is no reason to look for them
        package_count = -1

        for lineNumber in range(len(fileLines)):

            token_list = fileLines[lineNumber].split()

            # ignore very short lines
            if len(token_list) < 2:
              continue

            # ignore lines that begin with comments
            if token_list[0][:2] == "--" or token_list[0][:2] == "//" or token_list[0][:2] == "##":
              continue

            # usage only, no creates, replace, force views packages functions or procedures
            usage_flag = 1
            for token_index in range(len(token_list)):

                # look for CREATE VIEW, REPLACE VIEW, FORCE VIEW, making sure enough tokens exist
                if len(token_list) > token_index+1 \
                and token_list[token_index+1].upper() == "VIEW" \
                and (token_list[token_index].upper() == "CREATE" \
                or token_list[token_index].upper() == "REPLACE" \
                or token_list[token_index].upper() == "FORCE"):
                    # we are creating, forcing, or replacing - not using.  Set flag to 0
                    usage_flag = 0

                # look for PACKAGE BODY x IS, making sure enough tokens exist
                if token_list[token_index].upper() == "PACKAGE" \
                and len(token_list) > token_index+2 \
                and token_list[token_index+1].upper() == "BODY":
                    package_count += 1 # set flag
                    usage_flag = 0
     
                # if a package definition was found, look for functions and procedures
                if package_count != -1:
                    # first find functions
                    if token_list[0] == "FUNCTION" and len(token_list) > 1:
                        usage_flag = 0
                    # now find procedures
                    if token_list[0] == "PROCEDURE" and len(token_list) > 1:
                        usage_flag = 0

                if usage_flag == 0:
                    continue

            # Loop through all previously found views and packages to see if they are used in this line of text
            for inner_file_info in fileInfoList:

                # if this FileInfo instance has views
                if len(inner_file_info.viewInfoList) != 0:
                    for view_info in inner_file_info.viewInfoList:
                    # perform case insensitive find
                      if fileLines[lineNumber].upper().find(view_info.viewName.upper()) != -1:
                          if outer_file_info.fileName not in view_info.whereUsed.keys():
                              view_info.whereUsed[outer_file_info.fileName] = []
                              view_info.whereUsed[outer_file_info.fileName].append((outer_file_info, lineNumber))
                          else:
                              view_info.whereUsed[outer_file_info.fileName].append((outer_file_info, lineNumber))
                          # generate a unique number for use in making where used file if needed
                          if view_info.uniqueNumber == 0:
                              view_info.uniqueNumber = meta_info.NextIndex()


                # if this FileInfo instance has packages
                if len(inner_file_info.packageInfoList) != 0:
                    for package_info in inner_file_info.packageInfoList:

                    # perform case insensitive find, this is "package name"."function or procedure name"
                      if fileLines[lineNumber].upper().find(package_info.packageName.upper() + ".") != -1:

                        if outer_file_info.fileName not in package_info.whereUsed.keys():
                          package_info.whereUsed[outer_file_info.fileName] = []
                          package_info.whereUsed[outer_file_info.fileName].append((outer_file_info, lineNumber))
                        else:
                          package_info.whereUsed[outer_file_info.fileName].append((outer_file_info, lineNumber))
                          # generate a unique number for use in making where used file if needed
                        if package_info.uniqueNumber == 0:
                          package_info.uniqueNumber = meta_info.NextIndex()

                        #look for any of this packages' functions
                        for function_info in package_info.functionInfoList:
                          # perform case insensitive find
                          if fileLines[lineNumber].upper().find(package_info.packageName.upper() + "." \
                                              + function_info.functionName.upper()) != -1:
                            if outer_file_info.fileName not in function_info.whereUsed.keys():
                              function_info.whereUsed[outer_file_info.fileName] = []
                              function_info.whereUsed[outer_file_info.fileName].append((outer_file_info, lineNumber))
                            else:
                              function_info.whereUsed[outer_file_info.fileName].append((outer_file_info, lineNumber))
                              # generate a unique number for use in making where used file if needed
                              if function_info.uniqueNumber == 0:
                                function_info.uniqueNumber = meta_info.NextIndex()
                        #look for any of this packages procedures
                        for procedure_info in package_info.procedureInfoList:
                        # perform case insensitive find
                          if fileLines[lineNumber].upper().find(package_info.packageName.upper() + "." \
                                              + procedure_info.procedureName.upper()) != -1:
                            if outer_file_info.fileName not in procedure_info.whereUsed.keys():
                              procedure_info.whereUsed[outer_file_info.fileName] = []
                              procedure_info.whereUsed[outer_file_info.fileName].append((outer_file_info, lineNumber))
                            else:
                              procedure_info.whereUsed[outer_file_info.fileName].append((outer_file_info, lineNumber))
                              # generate a unique number for use in making where used file if needed
                              if procedure_info.uniqueNumber == 0:
                                procedure_info.uniqueNumber = meta_info.NextIndex()

    # print carriage return after last dot
    print

def GenerateCSSFile(meta_info):
    #FIXME: Just put this in a CSS file that is bundled and copied on run?
    CSSfile = meta_info.htmlDir + meta_info.css_FileName

    if os.path.exists(CSSfile):
        print meta_info.css_FileName + ' found, not generating'
    else:
        print meta_info.css_FileName + ' not found, generating!'

        outfile = open(meta_info.htmlDir + meta_info.css_FileName, "w")

        outfile.write("p {\n")
        outfile.write(" margin-left: 5%;\n")
        outfile.write(" font-family: Verdana, Arial, Helvetica, sans-serif;\n")
        outfile.write(" font-size: 12px;\n")
        outfile.write(" color: #000000;\n")
        outfile.write("}\n\n")

        outfile.write("p2 {\n")
        outfile.write(" margin-left: 20%;\n")
        outfile.write(" font-family: Verdana, Arial, Helvetica, sans-serif;\n")
        outfile.write(" font-size: 12px;\n")
        outfile.write(" color: #000000;\n")
        outfile.write("}\n\n")

        outfile.write("a {\n")
        outfile.write(" font-family: Verdana, Arial, Helvetica, sans-serif;\n")
        outfile.write(" color: #000099;\n")
        outfile.write("}\n\n")

        outfile.write("h1 {\n")
        outfile.write(" font-family: Lucida Grande, Arial Unicode MS, sans-serif;\n")
        outfile.write(" font-size: 20px;\n")
        outfile.write(" color: #000009;\n")
        outfile.write(" margin-left: auto;\n")
        outfile.write(" margin-right: auto;\n")
        outfile.write(" text-align: center;\n")
        outfile.write("}\n\n")

        outfile.write(".menu {\n")
        outfile.write(" align: center;\n")
        outfile.write(" font-family: Lucida Grande, Arial Unicode MS, sans-serif;\n")
        outfile.write(" font-size: 11px;\n")
        outfile.write(" color: #000000;\n")
        outfile.write(" text-align: center;\n")
        outfile.write("}\n\n")

        outfile.write(".footer {\n")
        outfile.write(" font-family: Lucida Grande, Arial Unicode MS, sans-serif;\n")
        outfile.write(" font-size: 9px;\n")
        outfile.write(" color: #000000;\n")
        outfile.write(" text-align: center;\n")
        outfile.write(" position: absolute, bottom;\n")
        outfile.write(" bottom: 0px;\n")
        outfile.write("}\n\n")

        outfile.write(".summary {\n")
        outfile.write(" font-family: Lucida Grande, Arial Unicode MS, sans-serif;\n")
        outfile.write(" font-size: 12px;\n")
        outfile.write(" color: #000000;\n")
        outfile.write(" text-align: left;\n")
        outfile.write(" position: relative;\n")
        outfile.write(" margin-left: 20%;\n")
        outfile.write("}\n\n")        

        outfile.write(".menu a:link {\n")
        outfile.write(" color: #336600;\n")
        outfile.write(" text-decoration: none;\n")
        outfile.write("}\n\n")

        outfile.write(".menu a:visited {\n")
        outfile.write(" color: #666666;\n")
        outfile.write(" text-decoration: none;\n")
        outfile.write("}\n\n")

        outfile.write(".menu a:hover {\n")
        outfile.write(" color: #990000;\n")
        outfile.write(" text-decoration: none;\n")
        outfile.write("}\n\n")

        outfile.write(".menu a:active {\n")
        outfile.write(" color: #666666;\n")
        outfile.write(" text-decoration: none;\n")
        outfile.write("}\n\n")

        outfile.close()  

def MakeHTMLHeader(meta_info):
    #FIXME put this header and footer in a config file
    s = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n'
    s += '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
    s += '<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">\n'
    s += '<head>\n  <link href="default.css" rel="stylesheet" type="text/css" />\n'
    s += '  <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />\n'
    s += '  <title>PeelDoc Documentation</title>\n'
    s += '</head>\n'
    s += '<body>\n'
    s += '  <p class="menu">\n'
    s += '    <a href="index.html">Home</a> | \n'
    s += '    <a href="' + metaInfo.packageIndex_FileName + '">Package Index</a> | \n'
    s += '    <a href="' + metaInfo.functionIndex_FileName + '">Function Index</a> | \n'
    s += '    <a href="' + metaInfo.procedureIndex_FileName + '">Procedure Index</a> | \n'
    s += '    <a href="' + metaInfo.packageFuncProdIndex_FileName + '">Full Package Listing</a> | \n'
    s += '    <a href="' + metaInfo.viewIndex_FileName + '">View Index</a> | \n'
    s += '    <a href="' + metaInfo.fileNoPathnamesIndex_FileName + '">Files by Name</a> | \n'
    s += '    <a href="' + metaInfo.fileWithPathnamesIndex_FileName + '">Files By Path</a>\n'
    s += '  </p>\n'
    return s

def MakeHTMLFooter(meta_info):
    s =  '  <p class="footer">\n'
    s += "    Generated on " + time.asctime(time.localtime(time.time())) + '\n'
    s += '    |  Licensed under GPL v3. Python Source (version ' + meta_info.versionString + ') available '
    s += '    <a href="' + os.path.split(meta_info.scriptName)[1] + '">here.</a>\n'
    s += '  </p>\n'
    s += "</body>\n</html>\n"
    return s

def CreateHTMLDirectory(metaInfo):
    # create the html directory if needed
    splitted = metaInfo.htmlDir.split(os.sep)
    temp = ""
    for path_element in splitted: # loop through path components, making directories as needed
        temp += path_element + os.sep
        if os.access(temp, os.F_OK) == 1:
            continue
        else:
            os.mkdir(temp)


def MakeFileIndexWithPathNames(meta_info):
    fileInfoList = meta_info.fileInfoList
    html_dir = meta_info.htmlDir
    outfilename = meta_info.fileWithPathnamesIndex_FileName

    filenametuplelist = []
    for file_info in fileInfoList:
        # skip all non-sql files
        if file_info.fileType != "sql":
            continue        
        filenametuplelist.append((file_info.fileName.upper(), file_info))
        filenametuplelist.sort(TupleCompareFirstElements)

    outfile = open(html_dir + outfilename, "w")
    outfile.write(MakeHTMLHeader(meta_info))
    outfile.write("<h1>Index Of All Files By Path Name</h1>\n<p>\n")

    for filenametuple in filenametuplelist:
        file_name = filenametuple[1].fileName
        temp = os.path.split(file_name)[1].replace(".", "_")
        temp += "_" + `filenametuple[1].uniqueNumber` + ".html"
        outfile.write("<a href=\"" + temp + "\">" + file_name[len(meta_info.topLevelDirectory)+1:])
        outfile.write("</a><br />\n")
        
    outfile.write("</p>")
    outfile.write(MakeHTMLFooter(meta_info))
    outfile.close()

def MakeFileIndexNoPathNames(meta_info):
    fileInfoList = meta_info.fileInfoList
    html_dir = meta_info.htmlDir
    outfilename = meta_info.fileNoPathnamesIndex_FileName

    filenametuplelist = []
    for file_info in fileInfoList:
        # skip all non-sql files
        if file_info.fileType != "sql":
            continue
        filenametuplelist.append((os.path.split(file_info.fileName)[1].upper(), file_info))
        filenametuplelist.sort(TupleCompareFirstElements)

    outfile = open(html_dir + outfilename, "w")
    outfile.write(MakeHTMLHeader(meta_info))
    outfile.write("<h1>Index Of All Files By File Name</h1>\n<p>\n")

    for filenametuple in filenametuplelist:
        file_name = filenametuple[1].fileName
        temp = os.path.split(file_name)[1].replace(".", "_")
        temp += "_" + `filenametuple[1].uniqueNumber` + ".html"
        outfile.write("<A href=\"" + temp + "\">" + os.path.split(file_name)[1])
        outfile.write("</A><br />\n")
    outfile.write("</p>\n")
    outfile.write(MakeHTMLFooter(meta_info))
    outfile.close()

def MakeViewIndex(meta_info):
    fileInfoList = meta_info.fileInfoList
    html_dir = meta_info.htmlDir
    outfilename = meta_info.viewIndex_FileName
    top_level_directory = meta_info.topLevelDirectory

    viewtuplelist = []
    for file_info in fileInfoList:
        # skip all non-sql files
        if file_info.fileType != "sql":
            continue        
        for view_info in file_info.viewInfoList:
            viewtuplelist.append((view_info.viewName.upper(), view_info, file_info)) # append as tuple for case insensitive sort
            viewtuplelist.sort(TupleCompareFirstElements)

        outfile = open(html_dir + outfilename, "w")
        outfile.write(MakeHTMLHeader(meta_info))
        outfile.write("<h1>Index Of All Views</h1>\n<p>\n")

        for view_tuple in viewtuplelist: # list of tuples describing every view
            # file name and line number as an HTML reference
            HTMLref = os.path.split(view_tuple[2].fileName)[1].replace(".", "_")
            HTMLref += "_" + `view_tuple[2].uniqueNumber` + ".html"
            HTMLref += "#" + `view_tuple[1].lineNumber`
            outfile.write("<A href=\"" + HTMLref + "\">" + view_tuple[1].viewName.lower() + "</A>\n")

            if len(view_tuple[1].whereUsed.keys()) > 0:
                    HTMLwhereusedref = "where_used_" + `view_tuple[1].uniqueNumber` + ".html"
                    outfile.write(" &nbsp;&nbsp; - <A href=\"" + HTMLwhereusedref + "\">where used list</A>\n")
            else:
                outfile.write(" &nbsp;&nbsp; - no use found\n")
                outfile.write("<br />\n")
                
        outfile.write("</p>\n")
        outfile.write(MakeHTMLFooter(meta_info))
        outfile.close()

def MakePackageIndex(meta_info):
    fileInfoList = meta_info.fileInfoList
    html_dir = meta_info.htmlDir
    outfilename = meta_info.packageIndex_FileName
    top_level_directory = meta_info.topLevelDirectory

    packagetuplelist = []
    for file_info in fileInfoList:
        # skip all non-sql files
        if file_info.fileType != "sql":
            continue        
        for package_info in file_info.packageInfoList:
            packagetuplelist.append((package_info.packageName.upper(), package_info, file_info)) # append as tuple for case insensitive sort

            packagetuplelist.sort(TupleCompareFirstElements)

        outfile = open(html_dir + outfilename, "w")
        outfile.write(MakeHTMLHeader(meta_info))
        outfile.write("<h1>Index Of All Packages</h1>\n<p>\n")

        for package_tuple in packagetuplelist: # list of tuples describing every package
        # file name and line number as an HTML reference
          HTMLref = os.path.split(package_tuple[2].fileName)[1].replace(".", "_")
          HTMLref += "_" + `package_tuple[2].uniqueNumber` + ".html"
          HTMLref += "#" + `package_tuple[1].lineNumber`
          outfile.write("<A href=\"" + HTMLref + "\">" + package_tuple[1].packageName.lower() + "</A>\n")
          if len(package_tuple[1].whereUsed.keys()) > 0:
                  HTMLwhereusedref = "where_used_" + `package_tuple[1].uniqueNumber` + ".html"
                  outfile.write(" &nbsp;&nbsp; - <A href=\"" + HTMLwhereusedref + "\">where used list</A>\n")
          else:
              outfile.write(" &nbsp;&nbsp; - no use found\n")
              outfile.write("\n")
        outfile.write("</p>\n")
        outfile.write(MakeHTMLFooter(meta_info))
        outfile.close()

def MakeFunctionIndex(meta_info):
    fileInfoList = meta_info.fileInfoList
    html_dir = meta_info.htmlDir
    outfilename = meta_info.functionIndex_FileName
    top_level_directory = meta_info.topLevelDirectory

    functiontuplelist = []
    for file_info in fileInfoList:
        # skip all non-sql files
        if file_info.fileType != "sql":
            continue        
        for package_info in file_info.packageInfoList:
            for function_info in package_info.functionInfoList:
                functiontuplelist.append((function_info.functionName.upper(), function_info, file_info, package_info)) # append as tuple for case insensitive sort

        functiontuplelist.sort(TupleCompareFirstElements)

        outfile = open(html_dir + outfilename, "w")
        outfile.write(MakeHTMLHeader(meta_info))
        outfile.write("<h1>Index Of All Functions</h1>\n<p>\n")

        for function_tuple in functiontuplelist: # list of tuples describing every function
          # file name and line number as an HTML reference
          HTMLref = os.path.split(function_tuple[2].fileName)[1].replace(".", "_")
          HTMLref += "_" + `function_tuple[2].uniqueNumber` + ".html"
          HTMLref += "#" + `function_tuple[1].lineNumber`
          outfile.write("<a href=\"" + HTMLref + "\">" + function_tuple[1].functionName.lower())
          outfile.write("</a> &nbsp;&nbsp; - from package " + function_tuple[3].packageName.lower() + "\n")
          if len(function_tuple[1].whereUsed.keys()) > 0:
                  HTMLwhereusedref = "where_used_" + `function_tuple[1].uniqueNumber` + ".html"
                  outfile.write(" &nbsp;&nbsp; - <a href=\"" + HTMLwhereusedref + "\">where used list</a><br />\n")
          else:
                outfile.write(" &nbsp;&nbsp; - no use found<br />\n")
                
        outfile.write("</p>\n")
        outfile.write(MakeHTMLFooter(meta_info))
        outfile.close()

def MakeProcedureIndex(meta_info):
    fileInfoList = meta_info.fileInfoList
    html_dir = meta_info.htmlDir
    outfilename = meta_info.procedureIndex_FileName
    top_level_directory = meta_info.topLevelDirectory

    proceduretuplelist = []
    for file_info in fileInfoList:
        # skip all non-sql files
        if file_info.fileType != "sql":
            continue        
        for package_info in file_info.packageInfoList:
            for procedure_info in package_info.procedureInfoList:
                proceduretuplelist.append((procedure_info.procedureName.upper(), procedure_info, file_info, package_info)) # append as tuple for case insensitive sort

        proceduretuplelist.sort(TupleCompareFirstElements)

        outfile = open(html_dir + outfilename, "w")
        outfile.write(MakeHTMLHeader(meta_info))
        outfile.write("<h1>Index Of All Procedures</h1>\n")

        for procedure_tuple in proceduretuplelist: # list of tuples describing every function

        # file name and line number as an HTML reference
          HTMLref = os.path.split(procedure_tuple[2].fileName)[1].replace(".", "_")
          HTMLref += "_" + `procedure_tuple[2].uniqueNumber` + ".html"
          HTMLref += "#" + `procedure_tuple[1].lineNumber`
          outfile.write("<A href=\"" + HTMLref + "\">" + procedure_tuple[1].procedureName.lower())
          outfile.write("</A> &nbsp;&nbsp; - from package " + procedure_tuple[3].packageName.lower() + "\n")
          if len(procedure_tuple[1].whereUsed.keys()) > 0:
              HTMLwhereusedref = "where_used_" + `procedure_tuple[1].uniqueNumber` + ".html"
              outfile.write(" &nbsp;&nbsp; - <A href=\"" + HTMLwhereusedref + "\">where used list</A>\n")
          else:
              outfile.write(" &nbsp;&nbsp; - no use found\n")
        outfile.write("</p>\n")
        outfile.write(MakeHTMLFooter(meta_info))
        outfile.close()

def MakePackagesWithFuncsAndProcsIndex(meta_info):
    fileInfoList = meta_info.fileInfoList
    html_dir = meta_info.htmlDir
    outfilename = meta_info.packageFuncProdIndex_FileName
    top_level_directory = meta_info.topLevelDirectory

    packagetuplelist = []
    for file_info in fileInfoList:
        # skip all non-sql files
        if file_info.fileType != "sql":
            continue        
        for package_info in file_info.packageInfoList:
          packagetuplelist.append((package_info.packageName.upper(), package_info, file_info)) # append as tuple for case insensitive sort

        packagetuplelist.sort(TupleCompareFirstElements)

        outfile = open(html_dir + outfilename, "w")
        outfile.write(MakeHTMLHeader(meta_info))
        outfile.write("<h1>Index Of All Packages, Their Functions And Procedures</h1>\n<p>\n")

        for package_tuple in packagetuplelist:
          # file name and line number as an HTML reference
          HTMLref = os.path.split(package_tuple[2].fileName)[1].replace(".", "_")
          HTMLref += "_" + `package_tuple[2].uniqueNumber` + ".html"
          HTMLref += "#" + `package_tuple[1].lineNumber`
          outfile.write("<br /><a href=\"" + HTMLref + "\">" + package_tuple[1].packageName.lower() + "</A>\n")
          if len(package_tuple[1].whereUsed.keys()) > 0:
                HTMLwhereusedref = "where_used_" + `package_tuple[1].uniqueNumber` + ".html"
                outfile.write(" &nbsp;&nbsp; - <A href=\"" + HTMLwhereusedref + "\">where used list</A>\n")
          else:
                outfile.write(" &nbsp;&nbsp;\n")
                outfile.write("<br />\n")

          # functions in this package
          functiontuplelist = []
          for function_info in package_tuple[1].functionInfoList:
            functiontuplelist.append((function_info.functionName.upper(), function_info, package_tuple[2])) # append as tuple for case insensitive sort

          functiontuplelist.sort(TupleCompareFirstElements)
          if len(functiontuplelist) != 0:
            outfile.write("<h2> Functions: </h2>\n")
          for function_tuple in functiontuplelist:
              HTMLref = os.path.split(function_tuple[2].fileName)[1].replace(".", "_")
              HTMLref += "_" + `function_tuple[2].uniqueNumber` + ".html"
              HTMLref += "#" + `function_tuple[1].lineNumber`
              outfile.write("<p> &nbsp;&nbsp;&nbsp;&nbsp;  &nbsp;&nbsp;&nbsp;&nbsp; ")
              outfile.write("<A href=\"" + HTMLref + "\">" + function_tuple[1].functionName.lower() + "</A>\n")
              if len(function_tuple[1].whereUsed.keys()) > 0:
                  HTMLwhereusedref = "where_used_" + `function_tuple[1].uniqueNumber` + ".html"
                  outfile.write(" &nbsp;&nbsp; - <A href=\"" + HTMLwhereusedref + "\">where used list</A></p>\n")
              else:
                  outfile.write(" &nbsp;&nbsp; - no use found by PeelDoc\n")
                  outfile.write("<BR>\n")

              # procedures in this package
              proceduretuplelist = []
              for procedure_info in package_tuple[1].procedureInfoList:
                proceduretuplelist.append((procedure_info.procedureName.upper(), procedure_info, package_tuple[2])) # append as tuple for case insensitive sort

                proceduretuplelist.sort(TupleCompareFirstElements)
                if len(proceduretuplelist) != 0:
                  outfile.write(" &nbsp;&nbsp;&nbsp;&nbsp; Procedures:<BR>\n")
                  for procedure_tuple in proceduretuplelist:
                        HTMLref = os.path.split(procedure_tuple[2].fileName)[1].replace(".", "_")
                        HTMLref += "_" + `procedure_tuple[2].uniqueNumber` + ".html"
                        HTMLref += "#" + `procedure_tuple[1].lineNumber`
                        outfile.write(" &nbsp;&nbsp;&nbsp;&nbsp;  &nbsp;&nbsp;&nbsp;&nbsp; ")
                        outfile.write("<A href=\"" + HTMLref + "\">" + procedure_tuple[1].procedureName.lower() + "</A>\n")
                        if len(procedure_tuple[1].whereUsed.keys()) > 0:
                            HTMLwhereusedref = "where_used_" + `procedure_tuple[1].uniqueNumber` + ".html"
                            outfile.write(" &nbsp;&nbsp; - <A href=\"" + HTMLwhereusedref + "\">where used list</A>\n")
                        else:
                            outfile.write(" &nbsp;&nbsp; - no use found by PeelDoc\n")
                            outfile.write("<BR>\n")
        outfile.write("</p>\n")
        outfile.write(MakeHTMLFooter(meta_info))
        outfile.close()


def CreateHyperlinkedSourceFilePages(meta_info):
    fileInfoList = meta_info.fileInfoList
    html_dir = meta_info.htmlDir
    top_level_directory = meta_info.topLevelDirectory

    dot_count = 1
    for file_info in fileInfoList:
        # skip all non-sql files
        if file_info.fileType != "sql":
            continue

        # print a . every file
        sys.stdout.write(".")
        sys.stdout.flush()
        if (dot_count % 60) == 0: # carriage return every 60 dots
            print
            sys.stdout.flush()
            dot_count += 1

        # read up the source file
        infile = open(file_info.fileName, "r")
        infile_line_list = infile.readlines()
        infile.close()

        # generate a file name for us to write to (+1 for delimiter)
        outfilename = os.path.split(file_info.fileName)[1].replace(".", "_")
        outfilename += "_" + `file_info.uniqueNumber` + ".html"

        # we need leading zeroes for the line numbers
        line_number_width = len(`len(infile_line_list)`) # number of chars in "number of lines of text"

        outfile = open(html_dir + outfilename, "w")
        outfile.write(MakeHTMLHeader(meta_info))
        outfile.write("<h1>" + file_info.fileName[len(top_level_directory)+1:] + "</h1>\n\n")

        outfile.write('<code><pre><br />')

        for line_number in range(len(infile_line_list)):
            zeroes = (1 + line_number_width - len(`line_number`)) * "0" # leading zeroes for line numbers
            outfile.write("<a name=\"" + `line_number` + "\"></a>") # hyperlink target
            outfile.write(zeroes + `line_number` + ": " + infile_line_list[line_number]) #text

        outfile.write("</pre></code><br />")
        outfile.write(MakeHTMLFooter(meta_info))
        outfile.close()
    print

def CreateIndexPage(meta_info):
    html_dir = meta_info.htmlDir
    script_name = meta_info.scriptName
    temp = str(int(meta_info.generationTime * 1000.0))

    outfile = open(html_dir + 'index.html', "w")
    outfile.write(MakeHTMLHeader(meta_info))

    outfile.write("  <h1>PeelDoc</h1>\n")
    outfile.write("  <p class=\"summary\">" + str(meta_info.fileCount) + " files found in " + meta_info.topLevelDirectory + "</p>\n")
    outfile.write("  <p class=\"summary\"> Generated successfully in " + temp + " milliseconds</p>\n")

    # Copy this source file to the HTML directory and link to it
    script_name_no_path = os.path.split(script_name)[1] # os.sep is path delimiter
    scriptinfile = open(script_name, "r")
    scriptoutfile = open(html_dir + script_name_no_path, "w")
    scriptoutfile.write(scriptinfile.read())
    scriptoutfile.close()
    scriptinfile.close()

    outfile.write(MakeHTMLFooter(meta_info))
    outfile.close()


def CreateWhereUsedPages(meta_info):
    html_dir = meta_info.htmlDir
    fileInfoList = meta_info.fileInfoList

    # loop through files
    dot_count = 1
    for file_info in fileInfoList:

        # skip all non-sql files
        if file_info.fileType != "sql":
            continue

      # print a . every file
        sys.stdout.write(".")
        sys.stdout.flush()
        if (dot_count % 60) == 0: # carriage return every 60 dots
          print
          sys.stdout.flush()
        dot_count += 1
  
        # loop through views
        for view_info in file_info.viewInfoList:

            if len(view_info.whereUsed.keys()) == 0:
                continue
            
            #open a "where used" file
            whereusedfilename = "where_used_" + `view_info.uniqueNumber` + ".html"
            outfile = open(html_dir + whereusedfilename, "w")
            
            # write our header
            outfile.write(MakeHTMLHeader(meta_info))               
            outfile.write("<h1>" + view_info.viewName + " Where Used List</h1>\n")

            # each where used
            where_used_keys = view_info.whereUsed.keys()
            where_used_keys.sort(CaseInsensitiveComparison)
            for key in where_used_keys:
                for whereusedtuple in view_info.whereUsed[key]:
                    line_number = whereusedtuple[1]
                    unique_number = whereusedtuple[0].uniqueNumber

                    # only make hypertext references for SQL files for now
                    if whereusedtuple[0].fileType == "sql":
                        outfile.write("<a href=\"" + os.path.split(key)[1].replace(".", "_"))
                        outfile.write("_" + `unique_number` + ".html" + "#" + `line_number` + "\">\n")
                        outfile.write(key[len(top_level_directory)+1:] + " line " + `line_number` + "</a><br />\n")
                    else:
                        outfile.write(key[len(top_level_directory)+1:] + " line " + `line_number` + "<br />\n")

            # footer and close
            outfile.write(MakeHTMLFooter(meta_info))
            outfile.close()

        for package_info in file_info.packageInfoList:

            if len(package_info.whereUsed.keys()) == 0:
                continue
            
            #open a "where used" file
            whereusedfilename = "where_used_" + `package_info.uniqueNumber` + ".html"
            outfile = open(html_dir + whereusedfilename, "w")
            
            # write our header
            outfile.write(MakeHTMLHeader(meta_info))               
            outfile.write("<h1>" + package_info.packageName + " Where Used List</h1>\n")


            # each where used
            where_used_keys = package_info.whereUsed.keys()
            where_used_keys.sort(CaseInsensitiveComparison)
            for key in where_used_keys:
                for whereusedtuple in package_info.whereUsed[key]:
                    line_number = whereusedtuple[1]
                    unique_number = whereusedtuple[0].uniqueNumber

                    # only make hypertext references for SQL files for now
                    if whereusedtuple[0].fileType == "sql":
                        outfile.write("<A href=\"" + os.path.split(key)[1].replace(".", "_"))
                        outfile.write("_" + `unique_number` + ".html" + "#" + `line_number` + "\">\n")
                        outfile.write(key[len(top_level_directory)+1:] + " &nbsp;&nbsp;line " + `line_number` + "</A><BR>\n")
                    else:
                        outfile.write(key[len(top_level_directory)+1:] + " &nbsp;&nbsp;line " + `line_number` + "<BR>\n")

            # footer and close
            outfile.write(MakeHTMLFooter(meta_info))
            outfile.close()

            #look for any of this packages' functions
            for function_info in package_info.functionInfoList:
                if len(function_info.whereUsed.keys()) == 0:
                    continue
                
                #open a "where used" file
                whereusedfilename = "where_used_" + `function_info.uniqueNumber` + ".html"
                outfile = open(html_dir + whereusedfilename, "w")
                
                # write our header
                outfile.write(MakeHTMLHeader(meta_info))               
                outfile.write("<h1>" + function_info.functionName.lower() + " </h1>from " + package_info.packageName)
                outfile.write(" <h1>Where Used List</h1>\n<p>\n")

                # each where used
                where_used_keys = function_info.whereUsed.keys()
                where_used_keys.sort(CaseInsensitiveComparison)
                for key in where_used_keys:
                    for whereusedtuple in function_info.whereUsed[key]:
                        line_number = whereusedtuple[1]
                        unique_number = whereusedtuple[0].uniqueNumber

                    # only make hypertext references for SQL files for now
                    if whereusedtuple[0].fileType == "sql":
                        outfile.write("<p><a href=\"" + os.path.split(key)[1].replace(".", "_"))
                        outfile.write("_" + `unique_number` + ".html" + "#" + `line_number` + "\">\n")
                        outfile.write(key[len(top_level_directory)+1:] + " &nbsp;&nbsp;line " + `line_number` + "</a></p>\n")
                    else:
                        outfile.write(key[len(top_level_directory)+1:] + " &nbsp;&nbsp;line " + `line_number` + "</p>\n")

                outfile.write("</p>\n")
                outfile.write(MakeHTMLFooter(meta_info))
                outfile.close()

            #look for any of this packages procedures
            for procedure_info in package_info.procedureInfoList:
                if len(procedure_info.whereUsed.keys()) == 0:
                    continue
                
                whereusedfilename = "where_used_" + `procedure_info.uniqueNumber` + ".html"
                outfile = open(html_dir + whereusedfilename, "w")
                
                outfile.write(MakeHTMLHeader(meta_info))               
                outfile.write("<CENTER><h1>" + procedure_info.procedureName.lower() + " </h1>from " + package_info.packageName.lower())
                outfile.write(" <h1>Where Used List</h1></CENTER><BR>\n")
                
                # each where used
                where_used_keys = procedure_info.whereUsed.keys()
                where_used_keys.sort(CaseInsensitiveComparison)
                for key in where_used_keys:
                    for whereusedtuple in procedure_info.whereUsed[key]:
                        line_number = whereusedtuple[1]
                        unique_number = whereusedtuple[0].uniqueNumber

                        # only make hypertext references for SQL files for now
                        if whereusedtuple[0].fileType == "sql":
                            outfile.write("<A href=\"" + os.path.split(key)[1].replace(".", "_"))
                            outfile.write("_" + `unique_number` + ".html" + "#" + `line_number` + "\">\n")
                            outfile.write(key[len(top_level_directory)+1:] + " &nbsp;&nbsp;line " + `line_number` + "</A><BR>\n")
                        else:
                            outfile.write(key[len(top_level_directory)+1:] + " &nbsp;&nbsp;line " + `line_number` + "<BR>\n")

                outfile.write(MakeHTMLFooter(meta_info))
                outfile.close()
    print

def print_usage():
  print "\n Usage: python PeelDoc.py path_to_files"
  print " Output is placed in current_directory/html/"


if __name__ == "__main__":

    metaInfo = MetaInfo()
    metaInfo.css_FileName = "default.css"
    metaInfo.fileWithPathnamesIndex_FileName = "FileNameIndexWithPathnames.html"
    metaInfo.fileNoPathnamesIndex_FileName = "FileNameIndexNoPathnames.html"
    metaInfo.viewIndex_FileName = "ViewIndex.html"
    metaInfo.packageIndex_FileName = "PackageIndex.html"
    metaInfo.functionIndex_FileName = "FunctionIndex.html"
    metaInfo.procedureIndex_FileName = "ProcedureIndex.html"
    metaInfo.packageFuncProdIndex_FileName = "PackagesWithFuncsAndProcsIndex.html"
    metaInfo.scriptName = sys.argv[0]
    metaInfo.htmlDir = os.path.split(sys.argv[0])[0] + os.sep + "html" + os.sep
    metaInfo.versionString = "0.1" 
    metaInfo.toDoList =''
    metaInfo.fileCount = 0
    metaInfo.generationTime = 0
    if len(sys.argv) < 2:
      print_usage()
      sys.exit(1)
    metaInfo.topLevelDirectory = sys.argv[1] #FIXME check that this is a valid path

    t1 = time.time()

    GenerateCSSFile(metaInfo) #Find / Generate default CSS file

    print "Scanning " + top_level_directory

    print "Creating file list" 
    FindFilesAndBuildFileList(metaInfo.topLevelDirectory, metaInfo.fileInfoList, metaInfo)

    print "Scanning for views and packages"
    ScanFilesForViewsAndPackages(metaInfo)

    print "Scanning for view and package usages"
    ScanFilesForWhereViewsAndPackagesAreUsed(metaInfo)

    print "Creating html subdirectory"
    CreateHTMLDirectory(metaInfo)

    print "Creating filename by path index"
    MakeFileIndexWithPathNames(metaInfo)

    print "Creating filename no path index"
    MakeFileIndexNoPathNames(metaInfo)

    print "Creating view index"
    MakeViewIndex(metaInfo)

    print "Creating package index"
    MakePackageIndex(metaInfo)

    print "Creating function index"
    MakeFunctionIndex(metaInfo)

    print "Creating procedure index"
    MakeProcedureIndex(metaInfo)

    print "Creating 'package with functions and procedures' index"
    MakePackagesWithFuncsAndProcsIndex(metaInfo)

    print "Creating 'where used' pages"
    CreateWhereUsedPages(metaInfo)

    print "Creating hyperlinked source file pages"
    CreateHyperlinkedSourceFilePages(metaInfo)

    t2 = time.time() #end time
    metaInfo.generationTime = t2-t1

    print "Creating site index page"
    CreateIndexPage(metaInfo)

    print "Generation Complete!"
