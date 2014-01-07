import unittest, time, sys
sys.path.extend(['.','..','py'])
import h2o, h2o_cmd, h2o_kmeans, h2o_hosts, h2o_import as h2i, h2o_jobs

DO_POLL=True
class Basic(unittest.TestCase):
    def tearDown(self):
        h2o.check_sandbox_for_errors()

    @classmethod
    def setUpClass(cls):
        global localhost
        localhost = h2o.decide_if_localhost()
        if (localhost):
            h2o.build_cloud(1)
        else:
            h2o_hosts.build_cloud_with_hosts(1)

    @classmethod
    def tearDownClass(cls):
        h2o.tear_down_cloud()

    def no_test_B_kmeans_benign(self):
        h2o.beta_features = True # fvec
        importFolderPath = "logreg"
        csvFilename = "benign.csv"
        hex_key = "benign.hex"

        csvPathname = importFolderPath + "/" + csvFilename
        # FIX! hex_key isn't working with Parse2 ? parseResult['destination_key'] not right?
        print "\nStarting", csvFilename
        parseResult = h2i.import_parse(bucket='smalldata', path=csvPathname, hex_key=hex_key, header=1, 
            timeoutSecs=180, doSummary=False)

        inspect = h2o_cmd.runInspect(None, parseResult['destination_key'])
        print "\nStarting", csvFilename

        expected = [
            ([8.86, 2.43, 35.53, 0.31, 13.22, 1.47, 1.33, 20.06, 13.08, 0.53, 2.12, 128.61, 35.33, 1.57], 49, None), 
            ([33.47, 2.29, 50.92, 0.34, 12.82, 1.33, 1.36, 21.43, 13.30, 0.37, 2.52, 125.40, 43.91, 1.79], 87, None), 
            ([27.64, 2.87, 48.11, 0.09, 11.80, 0.98, 1.51, 21.02, 12.53, 0.58, 2.89, 171.27, 42.73, 1.53], 55, None), 
            ([26.00, 2.67, 46.67, 0.00, 13.00, 1.33, 1.67, 21.56, 11.44, 0.22, 2.89, 234.56, 39.22, 1.56], 9, None), 
        ]

        # all are multipliers of expected tuple value
        allowedDelta = (0.01, 0.01, 0.01, 0.01)

        # loop, to see if we get same centers

        kwargs = {'k': 4, 'destination_key': 'benign_k.hex', 'seed': 265211114317615310, 'max_iter': 50}
        kmeans = h2o_cmd.runKMeans(parseResult=parseResult, timeoutSecs=5, **kwargs)

        #    kmeans['destination_key'] = 'benign_k.hex'
        ## h2o.verboseprint("kmeans result:", h2o.dump_json(kmeans))
        modelView = h2o.nodes[0].kmeans_model_view(model='benign_k.hex')
        h2o.verboseprint("KMeans2ModelView:", h2o.dump_json(modelView))
        model = modelView['model']
        clusters = model['centers']
        within_cluster_variances = model['within_cluster_variances']
        total_within_SS = model['total_within_SS']
        print "within_cluster_variances:", within_cluster_variances
        print "total_within_SS:", total_within_SS

        # make this fvec legal?
        (centers, tupleResultList) = h2o_kmeans.bigCheckResults(self, kmeans, csvPathname, parseResult, 'd', **kwargs)
        h2o_kmeans.compareResultsToExpected(self, tupleResultList, expected, allowedDelta, trial=0)


    def test_C_kmeans_prostate(self):
        h2o.beta_features = True # fvec

        importFolderPath = "logreg"
        csvFilename = "prostate.csv"
        hex_key = "prostate.hex"
        csvPathname = importFolderPath + "/" + csvFilename
        parseResult = h2i.import_parse(bucket='smalldata', path=csvPathname, hex_key=hex_key, header=1, timeoutSecs=180)
        inspect = h2o_cmd.runInspect(None, parseResult['destination_key'])
        print "\nStarting", csvFilename

        # loop, to see if we get same centers

        expected = [
            ([0.37,65.77,1.07,2.23,1.11,10.49,4.24,6.31], 215, 36955), 
            ([0.36,66.44,1.09,2.21,1.06,10.84,34.16,6.31], 136, 46045),
            ([0.83,66.17,1.21,2.86,1.34,73.30,15.57,7.31], 29, 33412),
        ]

        # all are multipliers of expected tuple value
        allowedDelta = (0.01, 0.01, 0.01)
        kwargs = {
            'ignored_cols': 'ID',
            'k': 3, 
            'initialization': 'Furthest', 
            'destination_key': 'prostate_k.hex', 
            'max_iter': 50,
            # reuse the same seed, to get deterministic results (otherwise sometimes fails
            'seed': 265211114317615310}

        # for fvec only?
        kmeans = h2o_cmd.runKMeans(parseResult=parseResult, timeoutSecs=5, noPoll=not DO_POLL, **kwargs)
        if not DO_POLL:
            h2o_jobs.pollWaitJobs(timeoutSecs=300, pollTimeoutSecs=300, retryDelaySecs=5)
            # hack..supposed to be there like va
            kmeans['destination_key'] = 'prostate_k.hex'
        # FIX! how do I get the kmeans result?
        ### print "kmeans result:", h2o.dump_json(kmeans)
        # can't do this
        # inspect = h2o_cmd.runInspect(key='prostate_k.hex')
        modelView = h2o.nodes[0].kmeans_model_view(model='prostate_k.hex')
        h2o.verboseprint("KMeans2ModelView:", h2o.dump_json(modelView))

        model = modelView['model']
        clusters = model['centers']
        within_cluster_variances = model['within_cluster_variances']
        total_within_SS = model['total_within_SS']
        print "within_cluster_variances:", within_cluster_variances
        print "total_within_SS:", total_within_SS
        # variance of 0 might be legal with duplicated rows. wasn't able to remove the duplicate rows of NAs at 
        # bottom of benign.csv in ec2
        # for i,c in enumerate(within_cluster_variances):
        #    if c < 0.1:
        #        raise Exception("cluster_variance %s for cluster %s is too small. Doesn't make sense. Ladies and gentlemen, this is Chewbacca. Chewbacca is a Wookiee from the planet Kashyyyk. But Chewbacca lives on the planet Endor. Now think about it...that does not make sense!" % (c, i))
        

        # make this fvec legal?
        (centers, tupleResultList) = h2o_kmeans.bigCheckResults(self, kmeans, csvPathname, parseResult, 'd', **kwargs)
        h2o_kmeans.compareResultsToExpected(self, tupleResultList, expected, allowedDelta, trial=0)


if __name__ == '__main__':
    h2o.unit_main()
