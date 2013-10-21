
Generalized Linear Model (GLM)
------------------------------

GLM includes several flexible algorithms. Each serves a 
different purpose, and is used under different assumptions.
Depending on function choice, it can be used either for 
prediction or classification.
 

**The GLM suite includes**

Gaussian regression
  
Poisson regression
  
binomial regression
  
gamma regression
  
Tweedie regression

  
  
Defining a GLM Model
""""""""""""""""""""

**Y:**
  Y is the model dependent variable (DV). In the context of each of
  the distinct link   functions Y variables are restricted in the
  following ways:

  *Gaussian* 
  Y variables must be continuous and real valued.

  *Binomial*
  Y variables are discrete and valued only at 0 or 1. 

  *Poisson*
  Y variables are discrete and valued strictly greater than 0. 

  *Gamma*
  Y variables are discrete and valued strictly greater than 0.
    
  
	
**X:** 
     
     This field will auto populate a list of the columns from the data
     set in use. The user selected set of X are the independent 
     variables on which the model predicts. H\ :sub:`2`\ O omits the dependent
     variable specified in Y, as well as any columns with a
     constant value. Constant columns are omitted because the variances
     of such columns are 0. In this case Y is independent of X, and X
     is not an explanatory variable.
   
     H\ :sub:`2`\ O factors (also called categorical variables or enumerators) as
     if they are collapsed columns of binomial variables at each
     factor level. When a factor is encountered, H\ :sub:`2`\ O determines the
     cardinality of the variable, and generates a unique regression
     coefficient for all but one of the factor levels. The omitted
     factor level becomes the reference level. H\ :sub:`2`\ O omits the first
     level in the ordered set. For instance, if factor levels are A, 
     B, and C, level A will be omitted. 

     Please note that H\ :sub:`2`\ O does not currently return a warning when
     users predict on data outside of the range on which the model was
     originally specified. It is the user's responsibility to ensure
     that out of data prediction is undertaken with caution.  
  

**Family and Link:**  
   
     Each of the given options differs in the
     assumptions made about the Y variable - the target of
     prediction. Each family is associated with a default link function,
     which defines the specialized transformation on the set of X
     variables chosen to  predict Y. 	

  *Gaussian (identity):* 
     
     Y are quantitative, continuous (or continuous
     predicted values can be meaningfully interpreted), and expected to
     be normally distributed 

  *Binomial (logit):* 

     Dependent variables take on two values,
     traditionally coded as 0 and 1, and follow a binomial distribution,
     can be understood as a categorical Y with two possible outcomes

  *Poisson (log):* 

     Dependent variable is a count - a quantitative,
     discrete value that expresses the number of times some event 
     occurred

  *Gamma (inverse):* 

     Dependent variable is a survival measure

**Lambda:**

      H\ :sub:`2`\ O provides a default value, but this can also be user
      defined. Lambda is a regularization parameter that is designed to
      prevent overfitting. The best value(s) of lambda depends on the
      desired level of agreement. 

**Alpha:**

      A user defined tuning regularization parameter.  H\ :sub:`2`\ O sets Alpha
      to 0.5 by default, but the parameter can take any value between
      0 and 1, inclusive. It functions such that there is an added
      penalty taken against the estimated fit of the model as the
      number of parameters increases. An alpha of 1 is the lasso
      penalty, and an alpha of 0 is the ridge penalty.
 
**Weight:**

      Allows the user to specify consideration given to
      observations based on the observed Y value. Weight=1 is
      neutral. Weight = 0.5 treats negative examples as twice more
      important than positive ones. Weight = 2.0 does the opposite.

**Case and Casemode:**

      These tuning parameters are used in combination when predicting
      binomial dependent variables. The default behavior of H\ :sub:`2`\ O is to 
      the Y variable can be specified, and the model can be asked to
      predict for observations above, below, or equal to this value. 
      Used in binomial prediction, where the default case is the mean of
      the Y column.  

Interpreting a Model
""""""""""""""""""""

**Degrees of Freedom:**

   *Null (total)* 
    Defined as (n-1), where n is the number of observations or rows
    in the data set. Quantity (n-1) is used rather than n to account
    for the condition that the residuals must sum to zero, which
    calls for a loss of one degree of freedom. 

   *Residual*  
    Defined as  (n-1)-p. This is the null degrees of freedom less the 
    number of parameters being estimated in the model. 

**Deviance:**

     The difference between the predicted value and the observed value 
     for each example or observation in the data. Deviance is
     a function of the specific model in question. Even when the same
     data set is used between two models, deviance statistics will
     change, because the predicted values of Y are model dependent. 
	
**Null Deviance:** 

     The deviance associated with the full model (also known as the
     saturated model). Heuristically, this can be thought of as the
     disturbance representing stochastic processes when all of
     determinants of Y are known and accounted for. 
 
**Residual Deviance:** 

      The deviance associated with the reduced model, a model defined
      by some subset of explanatory variables.   

**AIC:** 

     A model selection criterial that penalizes models having large
     numbers of predictors. AIC stands for Akiaike Information
     Criterion. It is defined as AIC = n ln SSEp - n ln n + 2p

**AUC:** 
 
     Area Under Curve. The curve in question is the
     receiver operating characteristic curve. The criteria is a 
     commonly  used metric for evaluating the performance of
     classifier models. It  gives the probability that a randomly
     chosen positive observation is correctly ranked greater than a
     randomly chosen negative observation. In machine learning, AUC is
     usually seen as the preferred evaluative criteria for a model
     (over accuracy) for classification models. AUC is not an output
     for Gaussian regression, but is output for classification models
     like binomial. 

**Confusion Matrix:** 

     The accuracy of the classifier can be evaluated
     from the confusion matrix, which reports actual versus predicted
     classifications, and the error rates of both.

Expert Settings
"""""""""""""""      
  Expert settings can be accessed by checking the tic box at the
  bottom of the model page. 

**Standardize** 

     An option that transforms variables into
     standardized variables, each with mean 0 and unit
     variance. Variables and coefficients are now expressed in terms
     of their relative position to 0, and in standard units. 

**Threshold** 

     An option only for binomial models that allows the user
     to define the degree to which they prefer to weight the
     sensitivity (the proportion of correctly classified 1s) and
     specificity (the proportion of correctly classified 0s). The
     default option is joint optimization for the overall
     classification rate. Changing this will alter the confusion
     matrix and the AUC.
 
**LSM Solver** 

     LSM stands for Least Squares Method. Least squares is
     the optimization criterion for the model residuals.

 
**Beta Epsilon** 

     Precision of the vector of coefficients. Computation
     stops when the maximal difference between two beta vectors is
     below than Beta epsilon

Validate GLM 
"""""""""""""

  After running the GLM Model, a .hex key associated with the model is
  generated.

#.  Select the "Validate on Another Dataset" option in the horizontal
    menu at the top of your results page. You can also access this at
    a later time by going to the drop down menu **Score** and
    selecting **GLM**.


#.  In the validation generation page enter the .hex key for the model
    you wish to validate in the Model Key field.

#.  In the key field enter the .hex for a testing data set matching
    the structure of your training data set. 

#.  Push the **Submit** button. 


Cross Validation
""""""""""""""""

     The model resulting from a GLM analysis in H\ :sub:`2`\ O can be
     presented with cross validated models at the user's request. The
     coefficients presented in the result model are independent of
     those in  any of the cross validated models, and are generated
     via least squares on the full data set. Cross validated models
     are generated by taking a 90% random subsample of the data,
     training a model, and testing that model on the remaining
     10%. This process is repeated as many times as the  user
     specifies in the Nfolds field during model specification. 


Cost of Computation
"""""""""""""""""""

H\ :sub:`2`\ O is able to process large data sets because it relies on
paralleled processes. Large data sets are divided into smaller
data sets and processed simultaneously, with results being
communicated between computers as needed throughout the process. 

In GLM data are split by rows, but not by columns because the
predicted Y values depend on information in each of the predictor
variable vectors. If we let O be a complexity function, N be the
number of observations (or rows), and P be the number of
predictors (or columns) then 

.. math::

   Runtime\propto p^3+\frac{(N*p^2)}{CPUs}

Distribution reduces the time it takes an algorithm to process
because it decreases N.
 

Relative to P, the larger that (N/CPUs) becomes, the more trivial
p becomes to the overall computational cost. However, when p is
greater than (N/CPUs), O is dominated by p.

.. math::

   Complexity = O(p^3 + N*p^2) 


References
""""""""""

Breslow, N E. "Generalized Linear Models: Checking Assumptions and
Strengthening Conclusions." Statistica Applicata 8 (1996): 23-41.

Frome, E L. "The Analysis of Rates Using Poisson Regression Models." 
Biometrics (1983): 665-674.
http://www.csm.ornl.gov/~frome/BE/FP/FromeBiometrics83.pdf

Goldberger, Arthur S. "Best Linear Unbiased Prediction in the
Generalized Linear Regression Model." Journal of the American
Statistical Association 57.298 (1962): 369-375.
http://people.umass.edu/~bioep740/yr2009/topics/goldberger-jasa1962-369.pdf

Guisan, Antoine, Thomas C Edwards Jr, and Trevor Hastie. "Generalized
Linear and Generalized Additive Models in Studies of Species
Distributions: Setting the Scene." Ecological modeling
157.2 (2002): 89-100. 
http://www.stanford.edu/~hastie/Papers/GuisanEtAl_EcolModel-2003.pdf

Nelder, John A, and Robert WM Wedderburn. "Generalized Linear Models."
Journal of the Royal Statistical Society. Series A (General) (1972): 370-384.
http://biecek.pl/MIMUW/uploads/Nelder_GLM.pdf

Pearce, Jennie, and Simon Ferrier. "Evaluating the Predictive
Performance of Habitat Models Developed Using Logistic Regression."
Ecological modeling 133.3 (2000): 225-245.
http://www.whoi.edu/cms/files/Ecological_Modelling_2000_Pearce_53557.pdf

Press, S James, and Sandra Wilson. "Choosing Between Logistic
Regression and Discriminant Analysis." Journal of the American
Statistical Association 73.364 (April, 2012): 699–705.
http://www.statpt.com/logistic/press_1978.pdf

Snee, Ronald D. "Validation of Regression Models: Methods and
Examples." Technometrics 19.4 (1977): 415-428.


 
  

	
