import unittest, random, sys, time, re, getpass
sys.path.extend(['.','..','py'])
import h2o, h2o_cmd, h2o_hosts, h2o_browse as h2b, h2o_import as h2i, h2o_glm, h2o_util
import h2o_print as h2p, h2o_gbm

# details:
# we want to seed a random dictionary for our enums
# string.ascii_uppercase string.printable string.letters string.digits string.punctuation string.whitespace
# restricting the choices makes it easier to find the bad cases
randChars = "abeE01" + "$%+-.;|\t "
randChars = "abeE01" # bad..causes NAification. probably 1E0e is causing a problem
# randChars = "abfF01" # try this.. fails
# randChars = "abcdef" #
quoteChars = "\'\""
# don't use any quote characters. We'd have to protect combinations
quoteChars = ""
MIN_ENUM_WIDTH = 2
MAX_ENUM_WIDTH = 5
assert MAX_ENUM_WIDTH > MIN_ENUM_WIDTH
RAND_ENUM_LENGTH = True
CUT_EXPR_CNT = 50
CUT_LOOP_CNT = 10

# minimize chance of repeats by making enough cut expressions
# as long as you have enough features and enums per features..should be random enough
assert CUT_EXPR_CNT > 2 * CUT_LOOP_CNT

if getpass.getuser()=='kevin': #10M
    ROWS=1000000 # 1M
    CAT_ITERATE = 8 # repeated cat to to get 2**N bigger
else: # 1M
    CAT_ITERATE = 6 # repeated cat to to get 2**N bigger
    ROWS=10000

assert CAT_ITERATE >= 1

DO_PLOT = getpass.getuser()=='kevin'

DO_MEDIAN = True
MAX_QBINS = 1000
MULTI_PASS = 1

# weights = [2,3,5]
#     d = random_data[h2o_util.weighted_choice(weights)]

def random_enum(width, randChars=randChars, quoteChars=quoteChars):
    # randomly return None 10% of the time
    # if random.randint(0,9)==0:
    #    return 'huh' # empty string doesn't work for exec compare?

    choiceStr = randChars + quoteChars
    mightBeNumberOrWhite = True
    while mightBeNumberOrWhite:
        # H2O doesn't seem to tolerate random single or double quote in the first two rows.
        # disallow that by not passing quoteChars for the first two rows (in call to here)
        r = ''.join(random.choice(choiceStr) for x in range(width))
        mightBeNumberOrWhite = h2o_util.might_h2o_think_number_or_whitespace(r)

    return r

def create_enum_list(n=4, minWidth=1, maxWidth=2, **kwargs):
    # Allowing length one, we sometimes form single digit numbers that cause the whole column to NA
    # see DparseTask.java for this effect
    # FIX! if we allow 0, then we allow NA?. I guess we check for no missing, so can't allow NA

    # list of unique random enums
    enumList = []
    while len(enumList)!= n:
        enum = random_enum(width=random.randint(int(minWidth), int(maxWidth)))
        if enum not in enumList:
            enumList.append(enum)
    return enumList

def create_col_enum_list(inCount):
    # the enum width is independent from the # of choices
    widthChoice = random.randint(MIN_ENUM_WIDTH, MAX_ENUM_WIDTH)

    MAX_CHOICES = 4
    weights = [1.0]
    numChoiceList = [2]
    # always need 2 choices since we do == and not equal
    for i in range(3, MAX_CHOICES):
        print "weights:", weights
        # each choice is 1/2th the previous
        w = weights[-1]/2.0
        assert w!=0
        weights.append(w)
        numChoiceList.append(i)
    
    print "numChoiceList", numChoiceList
    colEnumList = []
    for col in range(inCount):
        numChoice = numChoiceList[h2o_util.weighted_choice(weights)]
        print "numChoice:", numChoice
    
        # create the per-column choice lists
        enumList = create_enum_list(n=numChoice, minWidth=MIN_ENUM_WIDTH, maxWidth=widthChoice, quoteChars=quoteChars)
        colEnumList.append(enumList)
    return colEnumList
    

def write_syn_dataset(csvPathname, rowCount, inCount=1, outCount=1, SEED='12345678', 
        colSepChar=",", rowSepChar="\n", quoteChars="", colEnumList=None):
    r1 = random.Random(SEED)

    if CAT_ITERATE==0:
        dsf = open(csvPathname, "w+")
    else:
        tmpFd, tmpPathname = h2o.tmp_file("cat",".csv")
        dsf = open(tmpPathname, "w+")

    for row in range(rowCount):
        # doesn't guarantee that 10000 rows have 10000 unique enums in a column
        # essentially sampling with replacement
        rowData = []
        for iCol in range(inCount):
            # FIX! we should add some random NA?
            ri = random.choice(colEnumList[iCol])
            rowData.append(ri)

        # output columns. always 0-10e6 with 2 digits of fp precision
        for oCol in range(outCount):
            ri = "%.2f" % random.uniform(0, 10e6)
            rowData.append(ri)

        # use the new Hive separator
        rowDataCsv = colSepChar.join(map(str,rowData)) + rowSepChar
        ### sys.stdout.write(rowDataCsv)
        dsf.write(rowDataCsv)
    dsf.close()

    if CAT_ITERATE > 0:
        for c in range(CAT_ITERATE+1):
            if c==CAT_ITERATE:
                print "Doubling", tmpPathname, "into", csvPathname
                h2o_util.file_cat(tmpPathname, tmpPathname, csvPathname)
            else:
                tmp2Fd, tmp2Pathname = h2o.tmp_file()
                print "Doubling", tmpPathname, "into", tmp2Pathname
                h2o_util.file_cat(tmpPathname, tmpPathname, tmp2Pathname)
                tmpPathname = tmp2Pathname

    return colEnumList


class Basic(unittest.TestCase):
    def tearDown(self):
        h2o.check_sandbox_for_errors()

    @classmethod
    def setUpClass(cls):
        global SEED, localhost
        SEED = h2o.setup_random_seed()
        localhost = h2o.decide_if_localhost()
        if (localhost):
            h2o.build_cloud(1,java_heap_GB=14)
        else:
            h2o_hosts.build_cloud_with_hosts()

    @classmethod
    def tearDownClass(cls):
        # h2o.sleep(3600)
        h2o.tear_down_cloud()

    def test_exec_enums_rand_cut(self):
        h2o.beta_features = True
        SYNDATASETS_DIR = h2o.make_syn_dir()

        n = ROWS
        tryList = [
            (n, 10, 9, 'cE', 300), 
            ]

        # create key names to use for exec
        eKeys = ['e%s' % i for i in range(10)]

        # h2b.browseTheCloud()
        trial = 0
        for (rowCount, iColCount, oColCount, hex_key, timeoutSecs) in tryList:
            colCount = iColCount + oColCount

            hex_key = 'p'
            colEnumList = create_col_enum_list(iColCount)

            # create 100 possible cut expressions here, so we don't waste time below
            rowExprList = []
            print "Creating", CUT_EXPR_CNT, 'cut expressions'
            for i in range(CUT_EXPR_CNT):
                # init cutValue. None means no compare
                cutValue = [None for i in range(iColCount)]
                # build up a random cut expression
                MAX_COLS_IN_EXPR = iColCount-1
                cols = random.sample(range(iColCount-1), random.randint(1,MAX_COLS_IN_EXPR))
                for c in cols:
                    # possible choices within the column
                    cel = colEnumList[c]
                    # for now the cutValues are numbers for the enum mappings
                    if 1==1:
                        # FIX! hack. don't use encoding 0, maps to NA here? h2o doesn't like
                        celChoice = str(random.choice(range(len(cel))))
                    else:
                        celChoice = random.choice(cel)
                    cutValue[c] = celChoice
    
                cutExprList = []
                for i,c in enumerate(cutValue):
                    if c is None:   
                        continue
                    else:
                        # new ...ability to reference cols
                        # src[ src$age<17 && src$zip=95120 && ... , ]
                        # randomly pick == or !=
                        if random.randint(0,1)==0:
                            cutExprList.append('p$C'+str(i+1)+'!='+c)
                        else:
                            cutExprList.append('p$C'+str(i+1)+'=='+c)

                cutExpr = ' & '.join(cutExprList)
                # print "cutExpr:", cutExpr    

                rowExpr = '%s[%s,];' % (hex_key, cutExpr)
                # print "rowExpr:", rowExpr
                print rowExpr
                rowExprList.append(rowExpr)


            # CREATE DATASET*******************************************
            SEEDPERFILE = random.randint(0, sys.maxint)
            csvFilename = 'syn_enums_' + str(rowCount) + 'x' + str(colCount) + '.csv'
            csvPathname = SYNDATASETS_DIR + '/' + csvFilename

            print "Creating random", csvPathname
            write_syn_dataset(csvPathname, rowCount, iColCount, oColCount, SEEDPERFILE, colEnumList=colEnumList)

            # PARSE*******************************************************

            parseResult = h2i.import_parse(path=csvPathname, schema='put', hex_key=hex_key, timeoutSecs=30)
            print "Parse result['destination_key']:", parseResult['destination_key']
            inspect = h2o_cmd.runInspect(key=parseResult['destination_key'])
            h2o_cmd.infoFromInspect(inspect, csvPathname)
            # print h2o.dump_json(inspect)
            levels = h2o.nodes[0].levels(source=hex_key)
            print "levels result:", h2o.dump_json(levels)

            (missingValuesDict, constantValuesDict, enumSizeDict, colTypeDict, colNameDict) = \
                h2o_cmd.columnInfoFromInspect(parseResult['destination_key'], exceptionOnMissingValues=False)

            # error if any col has constant values
            if len(constantValuesDict) != 0:
                raise Exception("Probably got a col NA'ed and constant values as a result %s" % constantValuesDict)

            # INIT all possible key names used***************************
            # remember. 1 indexing!

            # is this needed?
            if 1==1:
                a = 'a=c(1,2,3);' + ';'.join(['a[,%s]=a[,%s-1]'% (i,i) for i in range(2,colCount)])
                print a
                for eKey in eKeys:
                    # build up the columns
                    e = h2o.nodes[0].exec_query(str='%s;%s=a' % (a, eKey), print_params=False)
                    ## print h2o.dump_json(e)


            xList = []
            eList = []
            fList = []
            for repeat in range(CUT_LOOP_CNT):
                # EXEC*******************************************************
                # don't use exec_expr to avoid issues with Inspect following etc.
                randICol = random.randint(0,iColCount-1)
                randOCol = random.randint(iColCount, iColCount+oColCount-1)

                # should be two different keys in the sample
                e = random.sample(eKeys,2)
                fKey = e[0]
                eKey = e[1]

                if 1==0:
                    start = time.time()
                    e = h2o.nodes[0].exec_query(str='%s=%s[,%s]' % (fKey, hex_key, randOCol+1))

                    elapsed = time.time() - start
                    print "exec 1 took", elapsed, "seconds."
                    execTime = elapsed

                if 1==1:
                    start = time.time()
                    h2o.nodes[0].exec_query(str="%s=%s" % (fKey, random.choice(rowExprList)))
                    elapsed = time.time() - start
                    execTime = elapsed
                    print "exec 2 took", elapsed, "seconds."
                
                if 1==0:
                    gKey = random.choice(eKeys)
                    # do a 2nd random to see if things blow up
                    start = time.time()
                    h2o.nodes[0].exec_query(str="%s=%s" % (gKey, fKey))
                    elapsed = time.time() - start
                    print "exec 3 took", elapsed, "seconds."

                if 1==1:
                    inspect = h2o_cmd.runInspect(key=fKey)
                    h2o_cmd.infoFromInspect(inspect, fKey)
                    numRows = inspect['numRows']
                    numCols = inspect['numCols']

                if numRows==0 or numCols!=colCount:
                    h2p.red_print("Warning: Cut resulted in", numRows, "rows and", numCols, "cols. Quantile will abort")

                # QUANTILE*******************************************************
                quantile = 0.5 if DO_MEDIAN else .999
                # first output col. always fed by an exec cut, so 0?
                column = iColCount
                start = time.time()
                q = h2o.nodes[0].quantiles(source_key=fKey, column=column, 
                    quantile=quantile, max_qbins=MAX_QBINS, multiple_pass=MULTI_PASS)
                h2p.red_print("quantile", quantile, q['result'])
                elapsed = time.time() - start
                print "quantile end on ", fKey, 'took', elapsed, 'seconds.'
                quantileTime = elapsed


                # remove all keys*******************************************************
                # what about hex_key?
                if 1==0:
                    start = time.time()
                    h2o.nodes[0].remove_all_keys()
                    elapsed = time.time() - start
                    print "remove all keys end on ", csvFilename, 'took', elapsed, 'seconds.'

                trial += 1
                xList.append(trial)
                eList.append(execTime)
                fList.append(quantileTime)


        # just get a plot of the last one (biggest)
        if DO_PLOT:
            xLabel = 'trial'
            eLabel = 'exec cut time'
            fLabel = 'quantile time'
            eListTitle = ""
            fListTitle = ""
            h2o_gbm.plotLists(xList, xLabel, eListTitle, eList, eLabel, fListTitle, fList, fLabel)



if __name__ == '__main__':
    h2o.unit_main()
