from utils import a2d, d2a

class refCollection(object):
    """
    This is a processed version of the Export File for it to be easier 
    processed by python
    """

    class classRefCollection(object):
        """
        Those are the reference for a class
        """
        def __init__(self, token, name):
            self.token = token
            self.name = name
            # three kinds of methods:
            # - virtual
            # - static
            # - interface
            self.virtualmethods = {}
            self.staticmethods = {}
            self.interfacemethods = {}
            self.constructors = {}
            # two kinds of fields:
            # - static
            # - instance
            self.staticfields = {}
            self.instancefields = {}

        def addStaticMethod(self, token, name):
            assert not token in self.staticmethods
            self.staticmethods[token] = name

        def getStaticMethod(self, token):
            print self.staticmethods.keys()
            return self.staticmethods[token]

        def addVirtualMethod(self, token, name):
            if "<init>" in name:
                assert self.token not in self.constructors
                self.constructors[token] = name
            else:
                assert not token in self.virtualmethods, self.virtualmethods[token]
                self.virtualmethods[token] = name

        def getVirtualMethod(self, token):
            return self.virtualmethods[token]

        def addInterfaceMethod(self, token, name):
            assert not token in self.interfacemethods
            self.interfacemethods[token] = name

        def export(self):
            struct = {}
            struct['token'] = self.token
            struct['name'] = self.name
            struct['virtualmethods'] = self.virtualmethods
            struct['staticmethods'] = self.staticmethods
            struct['interfacemethods'] = self.interfacemethods
            struct['constructors'] = self.constructors
            struct['staticfields'] = self.staticfields
            struct['instancefields'] = self.instancefields
            return struct

        def deroll(self, struct, name):
            dct = getattr(self, name)
            for token, name in struct[name].iteritems():
                dct[int(token)] = name

        @classmethod
        def impoort(cls, struct):
            slf = cls(struct['token'], struct['name'])
            
            slf.deroll(struct, 'virtualmethods')
            slf.deroll(struct, 'staticmethods')
            slf.deroll(struct, 'interfacemethods')
            slf.deroll(struct, 'constructors')
            slf.deroll(struct, 'staticfields')
            slf.deroll(struct, 'instancefields')
            return slf

    def __init__(self, AID, name):
        self.AID = AID
        self.name = name
        self.classes = {}

    def addClass(self, cls, CP):
        assert not cls.token in self.classes
        clsname = str(CP[CP[cls.name_index].name_index])
        clsname = clsname.split('/')[-1]
        self.classes[cls.token] = self.classRefCollection(cls.token, clsname)
        self.addclassFields(cls, CP)
        self.addclassMethods(cls, CP)

    def addclassFields(self, cls, CP):
        tmp = {}
        names = []
        for fld in cls.fields:
            tmp[fld.token] = fld
            if fld.token == 0xFF:
                # compile time constant field
                # not interesting
                continue
            fldname = str(CP[fld.name_index])
            if fldname in names:
                # name alread taken, so take extra steps
                if fldname in refs:
                    # save previous under another name
                    clstk, fldtk = refs[mtdname]
                    del refs[mtdname]
                    refs['$' + mtdname + '$' + str(CP[tmp[fldtk].descriptor_index])] = (cls.token, fldtk)
                refs['$' + mtdname + '$' + str(CP[mtd.descriptor_index])] = (cls.token, fld.token)
            else:
                refs[fldname] = (cls.token, fld.token)
            name.append(fldname)

    def addclassMethods(self, cls, CP):
        tmp = []
        names = {}
        for mtd in cls.methods:
            # First pass to look for name colision (type related)
            mtdname = str(CP[mtd.name_index])
            if mtdname in tmp:
                print "colision with %s" % mtdname
                mtdname = '$' + mtdname + '$' + str(CP[mtd.descriptor_index])
                print "renamed it %s" % mtdname
                names[mtd] = mtdname
            else:
                names[mtd] = mtdname
            tmp.append(mtdname)
        tmp = {}    
        for mtd in cls.methods:
            tmp[mtd.token] = mtd
            mtdname = names[mtd]
            if cls.isInterface:
                self.addInterfaceMethod(cls.token, mtd.token, mtdname)
            elif mtd.isStatic:
                self.addStaticMethod(cls.token, mtd.token, mtdname)
            else:
                self.addVirtualMethod(cls.token, mtd.token, mtdname)

    def addStaticMethod(self, clstoken, token, name):
        self.classes[clstoken].addStaticMethod(token, name)

    def getStaticMethod(self, clstoken, token):
        cls = self.classes[clstoken]
        return cls.name, cls.getStaticMethod(token)

    def addVirtualMethod(self, clstoken, token, name):
        self.classes[clstoken].addVirtualMethod(token, name)

    def addInterfaceMethod(self, clstoken, token, name):
        self.classes[clstoken].addInterfaceMethod(token, name)

    def populate(self, export_file):
        for cls in export_file.classes:
            self.addClass(cls, export_file.constant_pool)

    def export(self):
        """ return a JSON representation of this class """
        struct = {}
        struct['AID'] = d2a(self.AID)
        struct['name'] = self.name
        struct['classes'] = {}
        for key, value in self.classes.iteritems():
            struct['classes'][key] = value.export()
        return struct

    @classmethod
    def impoort(cls, struct):
        """ return a cls type with the content of the JSON string """
        slf = cls(a2d(struct['AID']), struct['name'])
        for token, claass in struct['classes'].iteritems():
            slf.classes[int(token)] = cls.classRefCollection.impoort(claass)
        return slf
        
    @classmethod
    def from_export_file(cls, export_file):
        CP = export_file.constant_pool
        slf = cls(a2d(export_file.AID), str(CP[CP[export_file.this_package].name_index]))
        slf.populate(export_file)
        return slf

def process(exp, options):
    if options.pretty_print:
        exp.pprint()
    return refCollection.from_export_file(exp).export()

def main():
    import os, json
    from exportfile import ExportFile
    from optparse import OptionParser

    parser = OptionParser(usage = "usage: %prog [options] PATH [PATH...]",
                          description = """\
This will process export file as generated by the Javacard converter.

The given path will be processed depending if it is a directory or a file.
If a directory all the export file found in the directory will be processed.
""")

    parser.add_option("-d", "--dump",
                      help    = "Dump the processed result to a pickle file.")

    parser.add_option("-P", "--pretty-print", default=False,
                      action="store_true", help= "Pretty print the results")

    parser.add_option("-v", "--verbose", default=False, action="store_true")

    parser.add_option("-i", "--impoort", help = "Import the dumped file")

    (options, args) = parser.parse_args()

    if options.impoort:
        f = open(options.impoort)
        s = json.loads(f.read())
        for pkg in s:
            refCollection.impoort(pkg)
        print "Import sucessfull !"
        return

    if len(args) == 0:
        parser.print_help()
        return

    res = []

    for path in args:
        if os.path.isdir(path):
            for dirname, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    if filename.endswith('.exp'):
                        if options.verbose: print "Processing %s" % os.path.join(dirname, filename)
                        # Good to go !
                        f = open(os.path.join(dirname, filename))
                        exp = ExportFile(f.read())
                        refs = process(exp, options)
                        res.append(refs)
        else:
            f = open(path)
            exp = ExportFile(f.read())
            refs = process(exp, options)
            res.append(refs)
    if options.dump is not None:
        f = open(options.dump, 'wb')
        f.write(json.dumps(res))

if __name__ == "__main__":
    main()
