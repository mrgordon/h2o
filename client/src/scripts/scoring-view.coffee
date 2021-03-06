Steam.ScoringView = (_, _scoring) ->
  _items = nodes$ []
  _hasExecuted = node$ no
  _comparisonTable = node$ null
  _hasComparisonTable = lift$ _comparisonTable, (table) -> not isNull table
  _modelSummary = nodes$ []

  createModelSummary = (scoring) ->
    score = if scoring.scores.length > 0 then head scoring.scores else null
    if score
      [
        key: 'Model Category'
        value: score.model.model_category
      ,
        key: 'Response Column'
        value: score.model.response_column_name
      ]
    else
      []

  createItem = (score) ->
    status = node$ if isNull score.status then '-' else score.status
    isSelected = lift$ status, (status) -> status is 'done'

    data: score
    algorithm: score.model.model_algorithm
    category: score.model.model_category
    responseColumn: score.model.response_column_name
    status: status
    time: node$ if isNull score.time then '-' else score.time
    canSelect: lift$ status, (status) -> status is 'done'
    isSelected: isSelected
    result: node$ score.result

  initialize = (scoring) ->
    _modelSummary createModelSummary scoring
    _items items = map scoring.scores, createItem
    if (every scoring.scores, (score) -> score.status is null)
      scoreModels scoring, items, ->
        forEach items, (item) ->
          apply$ item.isSelected, -> displayComparisonTable() if _hasExecuted()
        _hasExecuted yes
        displayComparisonTable()
    else
      _hasExecuted yes
      displayComparisonTable()

  runScoringJobs = (jobs, go) ->
    queue = copy jobs
    runNext = ->
      if job = shift queue
        job.run -> defer runNext
      else
        go()
    defer runNext

  scoreModels = (scoring, items, go) ->
    frameKey = scoring.frameKey
    jobs = map items, (item) ->
      modelKey = item.data.model.key
      item.status 'waiting'
      run: (go) ->
        item.status 'running'
        _.requestScoringOnFrame frameKey, modelKey, (error, result) ->

          if error
            _.error 'Scoring failed', { frameKey: frameKey, modelKey: modelKey }, error

          data = if error then error.data else result
          item.status if data.response then data.response.status else 'error'
          item.time if data.response then data.response.time else 0
          item.result error or result
          do go

    runScoringJobs jobs, ->
      forEach items, (item) ->
        score = item.data
        score.status = item.status()
        score.time = item.time()
        score.result = item.result()

      go()

  displayComparisonTable = () ->
    selectedItems = filter _items(), (item) -> item.canSelect() and item.isSelected()
    renderComparisonTable map selectedItems, (item) -> item.data

  renderRocCurve = (data) ->
    margin = top: 20, right: 20, bottom: 20, left: 30
    width = 175
    height = 175

    x = d3.scale.linear()
      .domain [ 0, 1 ]
      .range [ 0, width ]

    y = d3.scale.linear()
      .domain [ 0, 1 ]
      .range [ height, 0 ]

    axisX = d3.svg.axis()
      .scale x
      .orient 'bottom'
      .ticks 5

    axisY = d3.svg.axis()
      .scale y
      .orient 'left'
      .ticks 5

    line = d3.svg.line()
      .x (d) -> x d.fpr
      .y (d) -> y d.tpr

    el = document.createElementNS 'http://www.w3.org/2000/svg', 'svg'

    svg = (d3.select el)
      .attr 'class', 'y-roc-curve'
      .attr 'width', width + margin.left + margin.right
      .attr 'height', height + margin.top + margin.bottom
      .append 'g'
      .attr 'transform', "translate(#{margin.left},#{margin.top})"
    
    svg.append 'g'
      .attr 'class', 'x axis'
      .attr 'transform', "translate(0, #{height})"
      .call axisX
      .append 'text'
      .attr 'x', width
      .attr 'y', -6
      .style 'text-anchor', 'end'
      .text 'FPR'

    svg.append 'g'
      .attr 'class', 'y axis'
      .call axisY
      .append 'text'
      .attr 'transform', 'rotate(-90)'
      .attr 'y', 6
      .attr 'dy', '.71em'
      .style 'text-anchor', 'end'
      .text 'TPR'

    svg.append 'line'
      .attr 'class', 'guide'
      .attr 'stroke-dasharray', '3,3'
      .attr
        x1: x 0
        y1: y 0
        x2: x 1
        y2: y 1

    svg.selectAll '.dot'
      .data data
      .enter()
      .append 'circle'
      .attr 'class', 'dot'
      .attr 'r', 1
      .attr 'cx', (d) -> x d.fpr
      .attr 'cy', (d) -> y d.tpr

    svg.append 'path'
      .datum data
      .attr 'class', 'line'
      .attr 'd', line

    el

  computeTPRandFPR = (cm) ->
    [[tn, fp], [fn, tp]] = cm

    tpr: tp / (tp + fn)
    fpr: fp / (fp + tn)

  createRocCurve = (cms) ->
    rates = map cms, computeTPRandFPR
    renderRocCurve rates

  createInputParameter = (key, value, type) ->
    key: key, value: value, type: type, isDifferent: no

  combineInputParameters = (model) ->
    critical = mapWithKey model.critical_parameters, (value, key) ->
      createInputParameter key, value, 'critical'
    secondary = mapWithKey model.secondary_parameters, (value, key) ->
      createInputParameter key, value, 'secondary'
    concat critical, secondary

  # Side-effects!
  markAsDifferent = (parameterss, index) ->
    for parameters in parameterss
      parameters[index].isDifferent = yes
    return

  # Side-effects!
  compareInputParameters = (parameterss) ->
    headParameters = head parameterss
    tailParameterss = tail parameterss
    for parameters, index in headParameters
      for tailParameters in tailParameterss
        a = parameters.value
        b = tailParameters[index].value
        # DRF has array-valued params, so handle that case properly
        if (isArray a) and (isArray b)
          unless zipCompare a, b
            markAsDifferent parameterss, index
            break
        else
          if a isnt b
            markAsDifferent parameterss, index
            break
    return

  renderComparisonTable = (scores) ->
    [ div, table, kvtable, thead, tbody, tr, trExpert, diffSpan, th, thIndent, td, hyperlink] = geyser.generate words 'div table.table.table-condensed table.table-kv thead tbody tr tr.y-expert span.y-diff th th.y-indent td div.y-link'

    createParameterTable = ({ parameters }) ->
      kvtable [
        tbody map parameters, (parameter) ->
          trow = if parameter.type is 'critical' then tr else trExpert
          trow [
            th parameter.key
            td if parameter.isDifferent then diffSpan parameter.value else parameter.value
          ]
      ]

    createComparisonGrid = (scores) ->
      algorithmRow = [ th 'Method' ]
      nameRow = [ th 'Name' ]
      rocCurveRow = [ th 'ROC Curve' ]
      inputParametersRow = [
        th [
          (div 'Input Parameters')
          (hyperlink 'Show more', 'toggle-advanced-parameters')
        ]
      ]
      errorRow = [ th 'Error' ]
      aucRow = [ th 'AUC' ]
      thresholdCriterionRow = [ th 'Threshold Criterion' ]
      thresholdRow = [ thIndent 'Threshold' ]
      f1Row = [ thIndent 'F1' ]
      accuracyRow = [ thIndent 'Accuracy' ]
      precisionRow = [ thIndent 'Precision' ]
      recallRow = [ thIndent 'Recall' ]
      specificityRow = [ thIndent 'Specificity' ]
      maxPerClassErrorRow = [ thIndent 'Max Per Class Error' ]

      format4f = d3.format '.4f' # precision = 4

      #TODO what does it mean to have > 1 metrics
      scoreWithLowestError = min scores, (score) -> (head score.result.metrics).error_measure

      inputParamsWithAlgorithm = map scores, (score) ->
        algorithm: score.model.model_algorithm
        parameters: combineInputParameters score.model

      inputParamsByScoreIndex = map inputParamsWithAlgorithm, (a) -> a.parameters

      inputParamsByAlgorithm = values groupBy inputParamsWithAlgorithm, (a) -> a.algorithm
      # Side-effects!
      forEach inputParamsByAlgorithm, (groups) ->
        compareInputParameters map groups, (group) -> group.parameters

      for score, scoreIndex in scores
        model = score.model
        #TODO what does it mean to have > 1 metrics
        metrics = head score.result.metrics
        auc = metrics.auc
        cm = metrics.cm
        errorBadge = if scores.length > 1 and score is scoreWithLowestError then ' (Lowest)' else ''

        algorithmRow.push td model.model_algorithm
        nameRow.push td model.key
        rocCurveRow.push td 'Loading...', "roc-#{scoreIndex}"
        inputParametersRow.push td createParameterTable parameters: inputParamsByScoreIndex[scoreIndex]
        errorRow.push td (format4f metrics.error_measure) + errorBadge #TODO change to bootstrap badge
        aucRow.push td format4f auc.AUC
        thresholdCriterionRow.push td head auc.threshold_criteria
        thresholdRow.push td head auc.threshold_for_criteria
        f1Row.push td format4f head auc.F1_for_criteria
        accuracyRow.push td format4f head auc.accuracy_for_criteria
        precisionRow.push td format4f head auc.precision_for_criteria
        recallRow.push td format4f head auc.recall_for_criteria
        specificityRow.push td format4f head auc.specificity_for_criteria
        maxPerClassErrorRow.push td format4f head auc.max_per_class_error_for_criteria

      renderRocCurves = ($element) ->
        forEach scores, (score, scoreIndex) ->
          defer ->
            #TODO what does it mean to have > 1 metrics
            rocCurve = createRocCurve (head score.result.metrics).auc.confusion_matrices
            $("#roc-#{scoreIndex}", $element).empty().append rocCurve
        return

      toggleAdvancedParameters = ($element) ->
        isHidden = yes
        $toggleLink = $ '#toggle-advanced-parameters', $element
        $toggleLink.click ->
          if isHidden
            $('.y-expert', $element).show()
            $toggleLink.text 'Show less'
          else
            $('.y-expert', $element).hide()
            $toggleLink.text 'Show more'

          isHidden = not isHidden
          return
        return
      

      markup: table tbody [
        tr algorithmRow
        tr nameRow
        tr rocCurveRow
        tr inputParametersRow
        tr errorRow
        tr aucRow
        tr thresholdCriterionRow
        tr thresholdRow
        tr f1Row
        tr accuracyRow
        tr precisionRow
        tr recallRow
        tr specificityRow
        tr maxPerClassErrorRow
      ]
      behaviors: [ renderRocCurves, toggleAdvancedParameters ]

    _comparisonTable if scores.length > 0 then createComparisonGrid scores else null


  initialize _scoring

  items: _items
  modelSummary: _modelSummary
  hasExecuted: _hasExecuted
  comparisonTable: _comparisonTable
  hasComparisonTable: _hasComparisonTable
  caption: "Scoring on #{_scoring.frameKey}"
  timestamp: new Date(_scoring.timestamp).toString()
  template: 'scoring-view'
